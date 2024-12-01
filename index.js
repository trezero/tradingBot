const { PythonShell } = require('python-shell');

// Start the Python trading bot
const options = {
  mode: 'text',
  pythonPath: 'python',
  pythonOptions: ['-u'], // unbuffered output
  scriptPath: './src'
};

PythonShell.run('main.py', options).then(messages => {
  console.log('Trading bot started successfully');
}).catch(err => {
  console.error('Failed to start trading bot:', err);
});