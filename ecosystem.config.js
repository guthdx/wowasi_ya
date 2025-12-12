module.exports = {
  apps: [{
    name: 'wowasi_ya',
    script: '.venv/bin/python',
    args: '-m uvicorn wowasi_ya.main:app --host 0.0.0.0 --port 8002',
    cwd: '/home/guthdx/projects/wowasi_ya',
    env: {
      ENVIRONMENT: 'production'
    },
    watch: false,
    instances: 1,
    autorestart: true,
    max_memory_restart: '1G'  // Increased from 500M to accommodate document generation
  }]
}
