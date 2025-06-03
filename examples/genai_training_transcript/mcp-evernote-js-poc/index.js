#!/usr/bin/env node

const { Evernote } = require('evernote');
const readline = require('readline');
const https = require('https');
const crypto = require('crypto');
const { URL, URLSearchParams } = require('url');

function prompt(question) {
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

function base64URLEncode(buffer) {
  return buffer
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

async function main() {
  const clientId = process.env.EVERNOTE_CLIENT_ID;
  const redirectUri = process.env.EVERNOTE_REDIRECT_URI || 'urn:ietf:wg:oauth:2.0:oob';

  if (!clientId) {
    console.error('Please set EVERNOTE_CLIENT_ID environment variable (OAuth2 client ID).');
    console.error('See https://dev.evernote.com/doc/articles/authentication.php for details on obtaining OAuth2 credentials.');
    process.exit(1);
  }

  const codeVerifier = base64URLEncode(crypto.randomBytes(32));
  const codeChallenge = base64URLEncode(crypto.createHash('sha256').update(codeVerifier).digest());

  const authUrl = new URL('https://www.evernote.com/oauth2/authorize');
  authUrl.searchParams.append('client_id', clientId);
  authUrl.searchParams.append('response_type', 'code');
  authUrl.searchParams.append('redirect_uri', redirectUri);
  authUrl.searchParams.append('code_challenge', codeChallenge);
  authUrl.searchParams.append('code_challenge_method', 'S256');

  console.log('Authorize this app by visiting this URL:', authUrl.toString());

  const code = await prompt('Enter the OAuth2 authorization code: ');

  const params = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: redirectUri,
    client_id: clientId,
    code_verifier: codeVerifier,
  });

  const tokenResponse = await new Promise((resolve, reject) => {
    const req = https.request(
      'https://www.evernote.com/oauth2/token',
      { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' } },
      (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => resolve({ status: res.statusCode, body: data }));
      }
    );
    req.on('error', reject);
    req.write(params.toString());
    req.end();
  });

  if (tokenResponse.status < 200 || tokenResponse.status >= 300) {
    console.error('Error obtaining access token:', tokenResponse.body);
    process.exit(1);
  }

  let tokenJson;
  try {
    tokenJson = JSON.parse(tokenResponse.body);
  } catch (e) {
    console.error('Invalid JSON in token response:', tokenResponse.body);
    process.exit(1);
  }

  const accessToken = tokenJson.access_token;
  console.log('Access token obtained.');

  const client = new Evernote.Client({ token: accessToken });
  const noteStore = client.getNoteStore();
  const note = new Evernote.Types.Note();
  note.title = 'POC Test Note - ' + new Date().toISOString();
  note.content =
    '<?xml version="1.0" encoding="UTF-8"?>' +
    '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">' +
    '<en-note>This is a test note created by Evernote OAuth2 POC</en-note>';

  noteStore.createNote(accessToken, note, (err, createdNote) => {
    if (err) {
      console.error('Error creating note:', err);
      process.exit(1);
    }
    console.log('Note created with GUID:', createdNote.guid);

    noteStore.getNoteContent(accessToken, createdNote.guid, (err2, data) => {
      if (err2) {
        console.error('Error retrieving note content:', err2);
        process.exit(1);
      }
      console.log('Retrieved note content:', data);
      process.exit(0);
    });
  });
}

main();