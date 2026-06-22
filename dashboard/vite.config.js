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

        if (requestUrl.pathname === '/api/write/contract/ledger') {
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
              const auditPassed = payload.auditPassed
              const simulationPassed = payload.simulationPassed
              const ledgerPath = payload.ledgerPath
              const eventType = payload.eventType || 'dashboard_preview_action'

              if (!ledgerPath) {
                sendJson(res, 400, {
                  schema: 'bootforge.writer_safety_contract_ledger_append.v1',
                  status: 'failed',
                  error: 'Missing required parameter: ledgerPath is required in POST body.',
                })
                return
              }

              // Run usb_creator.py with contract validation and append ledger parameters
              const args = ['--validate-writer-contract']
              if (drivePath) args.push('--target-drive', drivePath)
              if (imagePath) args.push('--image', imagePath)
              if (auditPassed) args.push('--audit-passed')
              if (simulationPassed) args.push('--simulation-passed')
              args.push('--append-writer-contract-ledger', ledgerPath)

              runUsbCreator(
                args,
                {
                  schema: 'bootforge.writer_safety_contract_ledger_append.v1',
                  status: 'failed',
                  error: 'contract ledger append dev bridge failure — safe fallback',
                },
                res
              )
            } catch (err) {
              sendJson(res, 400, {
                schema: 'bootforge.writer_safety_contract_ledger_append.v1',
                status: 'failed',
                error: `Failed to parse POST body: ${err.message}`,
              })
            }
          })
          return
        }

        if (requestUrl.pathname === '/api/write/contract/export') {
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
              const auditPassed = payload.auditPassed
              const simulationPassed = payload.simulationPassed
              const exportPath = payload.exportPath
              const exportType = payload.exportType // json | markdown

              if (!exportPath || !exportType) {
                sendJson(res, 400, {
                  schema: 'bootforge.writer_safety_contract_export.v1',
                  status: 'failed',
                  error: 'Missing required parameters: exportPath and exportType are required in POST body.',
                })
                return
              }

              const args = ['--validate-writer-contract']
              if (drivePath) args.push('--target-drive', drivePath)
              if (imagePath) args.push('--image', imagePath)
              if (auditPassed) args.push('--audit-passed')
              if (simulationPassed) args.push('--simulation-passed')

              if (exportType === 'json') {
                args.push('--export-writer-contract-json', exportPath)
              } else if (exportType === 'markdown') {
                args.push('--export-writer-contract-markdown', exportPath)
              } else {
                sendJson(res, 400, {
                  schema: 'bootforge.writer_safety_contract_export.v1',
                  status: 'failed',
                  error: `Unsupported exportType '${exportType}'.`,
                })
                return
              }

              runUsbCreator(
                args,
                {
                  schema: 'bootforge.writer_safety_contract_export.v1',
                  status: 'failed',
                  error: 'contract export dev bridge failure — safe fallback',
                },
                res
              )
            } catch (err) {
              sendJson(res, 400, {
                schema: 'bootforge.writer_safety_contract_export.v1',
                status: 'failed',
                error: `Failed to parse POST body: ${err.message}`,
              })
            }
          })
          return
        }
        if (requestUrl.pathname === '/api/write/contract/readiness') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const drivePath = requestUrl.searchParams.get('drive')
          const imagePath = requestUrl.searchParams.get('image')
          const auditPassed = requestUrl.searchParams.get('auditPassed') === 'true'
          const simulationPassed = requestUrl.searchParams.get('simulationPassed') === 'true'
          const typedConfirmation = requestUrl.searchParams.get('typedConfirmation') || ''
          const destructiveAcknowledgement = requestUrl.searchParams.get('destructiveAcknowledgement') || ''

          const args = ['--final-writer-readiness-gate']
          if (drivePath) args.push('--target-drive', drivePath)
          if (imagePath) args.push('--image', imagePath)
          if (auditPassed) args.push('--audit-passed')
          if (simulationPassed) args.push('--simulation-passed')
          if (typedConfirmation) args.push('--typed-confirmation', typedConfirmation)
          if (destructiveAcknowledgement) args.push('--destructive-acknowledgement', destructiveAcknowledgement)

          runUsbCreator(
            args,
            {
              schema: 'bootforge.final_destructive_readiness_gate.v1',
              status: 'failed',
              error: 'contract readiness preview dev bridge failure — safe fallback',
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/write/hardware-preflight') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          const drivePath = requestUrl.searchParams.get('drive')
          const imagePath = requestUrl.searchParams.get('image')

          const args = ['--hardware-writer-preflight']
          if (drivePath) args.push('--target-drive', drivePath)
          if (imagePath) args.push('--image', imagePath)

          runUsbCreator(
            args,
            {
              schema: 'bootforge.hardware_writer_preflight.v1',
              status: 'failed',
              error: 'hardware writer preflight dev bridge failure — safe fallback',
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/write/target-identity-lock') {
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

              const args = ['--lock-removable-target']
              if (drivePath) args.push('--target-drive', drivePath)

              runUsbCreator(
                args,
                {
                  schema: 'bootforge.removable_target_identity_lock.v1',
                  status: 'failed',
                  error: 'target identity lock dev bridge failure — safe fallback',
                },
                res
              )
            } catch (err) {
              sendJson(res, 400, {
                schema: 'bootforge.removable_target_identity_lock.v1',
                status: 'failed',
                error: `Failed to parse POST body: ${err.message}`,
              })
            }
          })
          return
        }

        if (requestUrl.pathname === '/api/write/hardware-lab-permissions') {
          if (req.method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }
          runUsbCreator(
            ['--hardware-lab-permission-status'],
            {
              schema: 'bootforge.hardware_lab_permission_status.v1',
              status: 'failed',
              error: 'hardware lab permissions dev bridge failure — safe fallback',
            },
            res
          )
          return
        }

        if (requestUrl.pathname === '/api/write/physical-dryrun') {
          const method = req.method
          if (method !== 'POST' && method !== 'GET') {
            sendJson(res, 405, { error: 'Method not allowed' })
            return
          }

          if (method === 'GET') {
            const drivePath = requestUrl.searchParams.get('drive')
            const imagePath = requestUrl.searchParams.get('image')
            const args = ['--physical-writer-dryrun']
            if (drivePath) args.push('--target-drive', drivePath)
            if (imagePath) args.push('--image', imagePath)
            if (requestUrl.searchParams.get('mock') === 'true') {
              args.push('--mock-hardware-preflight')
            }
            runUsbCreator(
              args,
              {
                schema: 'bootforge.physical_writer_dryrun_result.v1',
                status: 'failed',
                error: 'physical writer dryrun dev bridge failure — safe fallback',
              },
              res
            )
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
              const auditPassed = payload.auditPassed
              const simulationPassed = payload.simulationPassed
              const typedConfirmation = payload.typedConfirmation
              const destructiveAcknowledgement = payload.destructiveAcknowledgement
              const mock = payload.mock

              const args = ['--physical-writer-dryrun']
              if (drivePath) args.push('--target-drive', drivePath)
              if (imagePath) args.push('--image', imagePath)
              if (auditPassed) args.push('--audit-passed')
              if (simulationPassed) args.push('--simulation-passed')
              if (typedConfirmation) args.push('--typed-confirmation', typedConfirmation)
              if (destructiveAcknowledgement) args.push('--destructive-acknowledgement', destructiveAcknowledgement)
              if (mock || payload.mockHardwarePreflight) args.push('--mock-hardware-preflight')

              runUsbCreator(
                args,
                {
                  schema: 'bootforge.physical_writer_dryrun_result.v1',
                  status: 'failed',
                  error: 'physical writer dryrun dev bridge failure — safe fallback',
                },
                res
              )
            } catch (err) {
              sendJson(res, 400, {
                schema: 'bootforge.physical_writer_dryrun_result.v1',
                status: 'failed',
                error: `Failed to parse POST body: ${err.message}`,
              })
            }
          })
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
