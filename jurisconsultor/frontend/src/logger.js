// A simple logger utility.
// Can be extended to send logs to a remote service.

const logger = {
  log: (...args) => {
    console.log(...args);
  },
  warn: (...args) => {
    console.warn(...args);
  },
  error: (...args) => {
    // In the future, we could send this to a logging service
    // like Sentry, LogRocket, etc.
    console.error(...args);
  },
};

export default logger;
