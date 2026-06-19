import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { execFile } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '..')
const usbCreatorPath = path.join(repoRoot, 'usb_creator.py')

function usbCreatorBridgePlugin() {
  return {
    name: 'phoenixcore-usb-creator-bridge',
    configureServer(server) {
      server.middlewares.use('/api/usb/scan', (req, res) => {
        if (req.method !== 'GET') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }

        const pythonCommand = process.env.PHOENIXCORE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3')

        execFile(
          pythonCommand,
          [usbCreatorPath, '--list-json'],
          {
            cwd: repoRoot,
            timeout: 15000,
            windowsHide: true,
            maxBuffer: 1024 * 1024,
          },
          (error, stdout, stderr) => {
            res.setHeader('Content-Type', 'application/json')

            if (error) {
              res.statusCode = 500
              res.end(JSON.stringify({
                schema: 'bootforge.drive_scan.v1',
                safe_mode: true,
                destructive: false,
                operation: 'read_only_drive_scan',
                drives: [],
                error: error.message,
                stderr: stderr?.trim() || '',
              }, null, 2))
              return
            }

            try {
              JSON.parse(stdout)
              res.statusCode = 200
              res.end(stdout)
            } catch (parseError) {
              res.statusCode = 500
              res.end(JSON.stringify({
                schema: 'bootforge.drive_scan.v1',
                safe_mode: true,
                destructive: false,
                operation: 'read_only_drive_scan',
                drives: [],
                error: `USB scan bridge returned invalid JSON: ${parseError.message}`,
                raw_stdout: stdout,
                stderr: stderr?.trim() || '',
              }, null, 2))
            }
          }
        )
      })
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), usbCreatorBridgePlugin()],
})
