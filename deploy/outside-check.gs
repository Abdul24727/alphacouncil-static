/**
 * Outside check for alphacouncil.tech (docs/production.md, "Outside check"). A Google Apps Script
 * project in the owner's Google account: it runs on Google's servers, away from the server it
 * watches, and needs no other account.
 *
 * - Every 5 minutes (a time-driven trigger) it fetches https://alphacouncil.tech/home and
 *   /api/v1/health the way a visitor would.
 * - The server's monitor (scripts/prod-monitor.py) posts to this project's web app at the end of
 *   every round (PING_URL in /etc/alphacouncil-platform/prod/monitor.env), or to PING_URL/fail when
 *   the round had an alert it could not email (the mail server refused, or a mail limit was reached).
 *
 * It emails the account's own address when the site fails 2 rounds in a row (the server or its
 * network is down, or the site is broken), when the monitor's pings stop for 15 minutes while the site
 * still answers (the monitor itself stopped), and when a /fail ping arrives; and once more when each
 * clears. At most MAILS_PER_DAY emails in 24 hours.
 *
 * Set up once: paste this file into a new project at script.google.com (replacing Code.gs), run
 * setup() and allow what it asks, then Deploy > New deployment > Web app, Execute as: Me, Who has
 * access: Anyone. The web app URL is the PING_URL (scripts/install-monitoring.sh --ping). Anyone
 * holding that URL can ping, so it is kept like a key: never in logs or commits.
 */

var SITE = 'alphacouncil.tech';
var URLS = ['https://alphacouncil.tech/home', 'https://alphacouncil.tech/api/v1/health'];
var FAILS_BEFORE_ALERT = 2;
var PING_SILENT_MS = 15 * 60 * 1000; // 3 missed rounds of the server's monitor
var MAILS_PER_DAY = 20;

function props_() {
  return PropertiesService.getScriptProperties();
}

function load_() {
  var raw = props_().getProperty('state');
  return raw ? JSON.parse(raw) : { siteFails: 0, siteAlerted: false, lastPing: 0, silentAlerted: false, failAlerted: false, sent: [] };
}

function save_(state) {
  props_().setProperty('state', JSON.stringify(state));
}

function when_(ms) {
  return Utilities.formatDate(new Date(ms), 'Asia/Riyadh', "yyyy-MM-dd HH:mm 'Riyadh'");
}

function mail_(state, subject, body) {
  var now = Date.now();
  state.sent = (state.sent || []).filter(function (t) { return t > now - 86400000; });
  if (state.sent.length >= MAILS_PER_DAY) {
    console.log('not emailed (daily limit reached): ' + subject);
    return false;
  }
  var to = props_().getProperty('ALERT_TO') || Session.getEffectiveUser().getEmail();
  MailApp.sendEmail({
    to: to,
    subject: '[' + SITE + '] ' + subject,
    name: SITE + ' outside check',
    body: body + '\n\n--\nSent by the outside check (Google Apps Script) at ' + when_(now) + '.\n' +
      'It fetches alphacouncil.tech every 5 minutes from Google\'s servers and listens for the server\'s\n' +
      'monitor. What each alert means: docs/production.md, "Outside check".',
  });
  state.sent.push(now);
  console.log('emailed: ' + subject);
  return true;
}

/** One visitor's view of the site: a list of what is wrong (empty: all fine). */
function probe_() {
  var problems = [];
  URLS.forEach(function (url) {
    var started = Date.now();
    try {
      var r = UrlFetchApp.fetch(url, {
        muteHttpExceptions: true,
        followRedirects: true,
        headers: { 'User-Agent': 'alphacouncil-outside-check/1 (Google Apps Script)' },
      });
      var code = r.getResponseCode();
      if (code !== 200) {
        problems.push(url + ' answered HTTP ' + code);
      } else if (/\/health$/.test(url)) {
        var status = null;
        try { status = JSON.parse(r.getContentText()).status; } catch (e) { /* not JSON */ }
        if (status !== 'ok') problems.push(url + ' answered 200 but its status is ' + JSON.stringify(status));
      }
    } catch (e) {
      problems.push(url + ' did not answer: ' + e.message + ' (after ' + Math.round((Date.now() - started) / 1000) + ' s)');
    }
  });
  return problems;
}

/** The 5-minute round (the time-driven trigger). */
function check() {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var state = load_();
    var now = Date.now();
    var problems = probe_();
    if (problems.length) {
      state.siteFails = (state.siteFails || 0) + 1;
      state.lastProblem = problems.join('\n');
      if (state.siteFails >= FAILS_BEFORE_ALERT && !state.siteAlerted) {
        state.siteAlerted = mail_(state, 'Problem: alphacouncil.tech fails when checked from outside',
          'Seen from Google\'s servers, ' + state.siteFails + ' checks in a row (5 minutes apart):\n\n' +
          problems.join('\n') + '\n\nIf the server\'s own monitor also emails, the server is up and the site is ' +
          'broken there; if it does not, the server or its network is down.');
      }
    } else {
      if (state.siteAlerted) {
        mail_(state, 'Recovered: alphacouncil.tech works from outside again',
          'Both https://alphacouncil.tech/home and /api/v1/health answered 200 again.\n\nWhat was wrong:\n' + (state.lastProblem || ''));
      }
      state.siteFails = 0;
      state.siteAlerted = false;
    }
    // The server's monitor: silent for 15 minutes once it has pinged at least once.
    // While the site itself fails from outside, that alert already says the server may be down.
    if (state.lastPing && now - state.lastPing > PING_SILENT_MS && !state.silentAlerted && !problems.length) {
      state.silentAlerted = mail_(state, 'Problem: the server\'s monitor has gone quiet',
        'The monitor on the server (acp-prod-monitor, every 5 minutes) last checked in at ' + when_(state.lastPing) + '.\n' +
        'The site still answers from outside, so the server is up and the monitor itself stopped:\n' +
        '  ssh root@alphacouncil.tech systemctl status acp-prod-monitor.timer acp-prod-monitor.service');
    }
    save_(state);
  } finally {
    lock.releaseLock();
  }
}

/** The server's monitor checks in: PING_URL after every round, PING_URL/fail when it could not email. */
function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var state = load_();
    var failed = String((e && e.pathInfo) || '').replace(/^\/+|\/+$/g, '') === 'fail';
    var text = String((e && e.postData && e.postData.contents) || '').slice(0, 5000);
    if (state.silentAlerted) {
      mail_(state, 'Recovered: the server\'s monitor checks in again',
        'The monitor on the server checked in again after a silence since ' + when_(state.lastPing) + '.');
      state.silentAlerted = false;
    }
    state.lastPing = Date.now();
    if (failed && !state.failAlerted) {
      state.failAlerted = mail_(state, 'Problem: the server\'s monitor could not send an alert',
        'The monitor on the server had news it could not email (its mail server refused, or its mail limit\n' +
        'was reached). Its round said:\n\n' + text);
    } else if (!failed && state.failAlerted) {
      mail_(state, 'Recovered: the server\'s monitor can email again', 'Its round said:\n\n' + text);
      state.failAlerted = false;
    }
    save_(state);
  } finally {
    lock.releaseLock();
  }
  return ContentService.createTextOutput('ok');
}

/** Run once from the editor: installs the 5-minute trigger, runs one round, sends a test email. */
function setup() {
  ScriptApp.getProjectTriggers().forEach(function (t) {
    if (t.getHandlerFunction() === 'check') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('check').timeBased().everyMinutes(5).create();
  props_().setProperty('ALERT_TO', Session.getEffectiveUser().getEmail());
  check();
  var state = load_();
  mail_(state, 'Test: the outside check is on',
    'This is a test of the alphacouncil.tech outside check. Nothing is wrong because of it.\n\n' +
    'From now on this address gets an email when:\n' +
    '  - alphacouncil.tech/home or /api/v1/health fails 2 checks in a row from Google\'s servers,\n' +
    '  - the server\'s monitor stops checking in for 15 minutes,\n' +
    '  - the server\'s monitor had an alert it could not email,\n' +
    'and once more when each clears.\n\nThe site right now: ' +
    (state.siteFails ? 'NOT answering:\n' + state.lastProblem : 'both pages answered 200.'));
  save_(state);
  console.log('setup done: trigger every 5 minutes, alerts to the account\'s address');
}

/** From the editor: the state as it stands (no URLs, no addresses). */
function status() {
  var s = load_();
  console.log(JSON.stringify({
    siteFails: s.siteFails, siteAlerted: s.siteAlerted, failAlerted: s.failAlerted, silentAlerted: s.silentAlerted,
    lastPing: s.lastPing ? when_(s.lastPing) : 'never', mailsIn24h: (s.sent || []).filter(function (t) { return t > Date.now() - 86400000; }).length,
    triggers: ScriptApp.getProjectTriggers().map(function (t) { return t.getHandlerFunction(); }),
  }));
}
