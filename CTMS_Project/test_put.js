const fs = require('fs');
const token = fs.readFileSync('token.txt', 'utf8').trim();
fetch('http://localhost:3000/ctms/documents/76d34d55-7af5-46cf-8fc4-2f3625d6a44a', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  },
  body: JSON.stringify({
    "projectId": "2bc823c9-0a9f-442b-b8c1-32a9d126b04e",
    "tmfSection": "section_00_general",
    "documentCode": "TMF-019",
    "documentName": "test updated",
    "documentType": "other",
    "description": "",
    "isRequired": false
  })
}).then(r => r.json()).then(console.log).catch(console.error);