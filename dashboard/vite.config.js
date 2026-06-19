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

        next()
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), usbCreatorBridgePlugin()],
})
