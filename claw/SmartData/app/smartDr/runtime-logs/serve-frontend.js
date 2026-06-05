const express = require('express');
const path = require('path');

const app = express();
const port = Number(process.env.PORT || 8080);

app.use(express.static(path.resolve(__dirname, '..', 'frontend')));

app.listen(port, () => {
  console.log(`frontend running on ${port}`);
});
