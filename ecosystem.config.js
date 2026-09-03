module.exports = {
  apps: [
    {
      name: "moviebox-api",
      script: "./main.py",
      interpreter: "./venv/bin/python",
      env: {
        PORT: 8000,
        WORKERS: 8
      },
      autorestart: true,
      watch: false,
      max_memory_restart: "1G"
    }
  ]
};
