import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { execFile } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..')
const usbCreatorPath = path.join(repoRoot, 'usb_creator.py')
const pythonCommand = process.env.PHOENIXCORE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3')

function sendJson(res, statusCode, payload) {
  res.statusCode = statusCode
  res.setHeader('Content-Type', 'application/json')
  res.end(JSON.stringify(payload, null, 2))
}

function runUsbCreator(args, fallbackPayload, res) {
  execFile(
    pythonCommand,
    [usbCreatorPath, ...args],
    {
      cwd: repoRoot,
      timeout: 60000,
      windowsHide: true,
      maxBuffer: 1024 * 1024 * 4,
    },
    (error, stdout, stderr) => {
      res.setHeader('Content-Type', 'application/json')

      if (error) {
        sendJson(res, 500, {
          ...fallbackPayload,
          error: error.message,
          stderr: stderr?.trim() || '',
        })
        return
      }

      try {
        JSON.parse(stdout)
        res.statusCode = 200
        res.end(stdout)
      } catch (parseError) {
        sendJson(res, 500, {
          ...fallbackPayload,
          error: `USB creator bridge returned invalid JSON: ${parseError.message}`,
          raw_stdout: stdout,
          stderr: stderr?.trim() || '',
        })
      }
    }
  )
}

function usbCreatorBridgePlugin() {
  return {
    name: 'phoenixcore-usb-creator-bridge',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const requestUrl = new URL(req.url, 'http://localhost')

        if (requestUrl.pathname === '/api/usb/scan') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          runUsbCreator(
            ['--list-json'],
            {
              schema: 'bootforge.drive_scan.v1',
              safe_mode: true,
              destructive: false,
              operation: 'read_only_drive_scan',
              drives: [],
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/image/inspect') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const imagePath = requestUrl.searchParams.get('path')
          if (!imagePath) {
            sendJson(res, 400, {
              schema: 'bootforge.image_inspection.v1',
              safe_mode: true,
              destructive: false,
              operation: 'read_only_image_inspection',
              image: null,
              error: 'Missing required query parameter: path',
            })
            return
          }

          runUsbCreator(
            ['--inspect-image', imagePath],
            {
              schema: 'bootforge.image_inspection.v1',
              safe_mode: true,
              destructive: false,
              operation: 'read_only_image_inspection',
              image: null,
            },
            res
          )
          return
        }
        if (requestUrl.pathname === '/api/usb/safety') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const drivePath = requestUrl.searchParams.get('path')
          if (!drivePath) {
            sendJson(res, 400, {
              schema: 'bootforge.drive_safety.v1',
              safe_mode: true,
              destructive: false,
              operation: 'read_only_drive_safety_check',
              drive: null,
              error: 'Missing required query parameter: path',
            })
            return
          }

          runUsbCreator(
            ['--inspect-drive', drivePath],
            {
              schema: 'bootforge.drive_safety.v1',
              safe_mode: true,
              destructive: false,
              operation: 'read_only_drive_safety_check',
              drive: null,
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/write/plan') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const drivePath = requestUrl.searchParams.get('drive')
          const imagePath = requestUrl.searchParams.get('image')
          if (!drivePath || !imagePath) {
            sendJson(res, 400, {
              schema: 'bootforge.write_plan.v1',
              safe_mode: true,
              destructive: false,
              operation: 'dry_run_write_plan',
              actual_write_enabled: false,
              requires_future_confirmation: true,
              error: 'Missing required query parameters: drive and image are required.',
            })
            return
          }

          runUsbCreator(
            ['--plan-write', '--target-drive', drivePath, '--image', imagePath],
            {
              schema: 'bootforge.write_plan.v1',
              safe_mode: true,
              destructive: false,
              operation: 'dry_run_write_plan',
              actual_write_enabled: false,
              requires_future_confirmation: true,
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/write/audit') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const drivePath = requestUrl.searchParams.get('drive')
          const imagePath = requestUrl.searchParams.get('image')
          if (!drivePath || !imagePath) {
            sendJson(res, 400, {
              schema: 'bootforge.write_plan_audit.v1',
              safe_mode: true,
              destructive: false,
              operation: 'dry_run_write_plan_audit',
              plan_id: null,
              plan_hash: null,
              validation_status: 'failed',
              eligible: false,
              blocked: true,
              block_reasons: ['Missing required query parameters: drive and image are required.'],
              checks: [],
              write_plan: {},
              error: 'Missing required query parameters: drive and image are required.',
            })
            return
          }

          runUsbCreator(
            ['--audit-plan', '--target-drive', drivePath, '--image', imagePath],
            {
              schema: 'bootforge.write_plan_audit.v1',
              safe_mode: true,
              destructive: false,
              operation: 'dry_run_write_plan_audit',
              plan_id: null,
              plan_hash: null,
              validation_status: 'failed',
              eligible: false,
              blocked: true,
              block_reasons: [],
              checks: [],
              write_plan: {},
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/write/export') {
          if (req.method !== 'POST') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          let body = ''
          req.on('data', (chunk) => {
            body += chunk
          })
          req.on('end', () => {
            try {
              const payload = JSON.parse(body || '{}')
              const drivePath = payload.drive
              const imagePath = payload.image
              const format = payload.format
              const exportPath = payload.path

              if (!drivePath || !imagePath || !format || !exportPath) {
                sendJson(res, 400, {
                  schema: 'bootforge.audit_export.v1',
                  safe_mode: true,
                  destructive: false,
                  operation: 'audit_evidence_export',
                  status: 'failed',
                  error: 'Missing required parameters: drive, image, format, and path are required in the POST body.',
                })
                return
              }

              const exportFlag = format === 'json' ? '--export-json' : '--export-markdown'
              runUsbCreator(
                ['--audit-plan', '--target-drive', drivePath, '--image', imagePath, exportFlag, exportPath],
                {
                  schema: 'bootforge.audit_export.v1',
                  safe_mode: true,
                  destructive: false,
                  operation: 'audit_evidence_export',
                  format: format,
                  export_path: exportPath,
                  status: 'failed',
                },
                res
              )
            } catch (parseError) {
              sendJson(res, 400, {
                schema: 'bootforge.audit_export.v1',
                safe_mode: true,
                destructive: false,
                operation: 'audit_evidence_export',
                status: 'failed',
                error: `Failed to parse POST body: ${parseError.message}`,
              })
            }
          })
          return
        }

        if (requestUrl.pathname === '/api/write/simulate') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const drivePath = requestUrl.searchParams.get('drive')
          const imagePath = requestUrl.searchParams.get('image')
          const failAtChunk = requestUrl.searchParams.get('failAtChunk')
          const cancelAtChunk = requestUrl.searchParams.get('cancelAtChunk')

          if (!drivePath || !imagePath) {
            sendJson(res, 400, {
              schema: 'bootforge.mock_writer.v1',
              safe_mode: true,
              destructive: false,
              operation: 'mock_writer_simulation',
              actual_write_enabled: false,
              target_type: 'null_device',
              error: 'Missing required query parameters: drive and image are required.',
            })
            return
          }

          const args = ['--simulate-write', '--target-drive', drivePath, '--image', imagePath]
          if (failAtChunk) {
            args.push('--mock-fail-at-chunk', failAtChunk)
          }
          if (cancelAtChunk) {
            args.push('--mock-cancel-at-chunk', cancelAtChunk)
          }

          runUsbCreator(
            args,
            {
              schema: 'bootforge.mock_writer.v1',
              safe_mode: true,
              destructive: false,
              operation: 'mock_writer_simulation',
              actual_write_enabled: false,
              target_type: 'null_device',
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/write/contract') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const drivePath = requestUrl.searchParams.get('drive')
          const imagePath = requestUrl.searchParams.get('image')
          const auditPassed = requestUrl.searchParams.get('auditPassed') === 'true'
          const simulationPassed = requestUrl.searchParams.get('simulationPassed') === 'true'

          const args = ['--validate-writer-contract']
          if (drivePath) args.push('--target-drive', drivePath)
          if (imagePath) args.push('--image', imagePath)
          if (auditPassed) args.push('--audit-passed')
          if (simulationPassed) args.push('--simulation-passed')

          runUsbCreator(
            args,
            {
              schema: 'bootforge.writer_safety_contract.v1',
              real_writer_implemented: false,
              destructive_operations_enabled: false,
              blocked: true,
              block_reasons: ['contract preview endpoint error — safe fallback'],
            },
            res
          )
          return
        }

        next()
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), usbCreatorBridgePlugin()],
})
