/**
 * plant_care: a small web app that lets the plant_care program keep a Google Tasks list.
 * It runs as you, only touches the list named "plant_care", and only answers calls that carry
 * the shared secret stored in Project Settings > Script properties > SHARED_SECRET.
 * Setup steps are in the README, section "Google reminders".
 */
var LIST_TITLE = 'plant_care';

function doPost(e) {
  var out;
  try {
    var body = JSON.parse(e.postData.contents);
    var secret = PropertiesService.getScriptProperties().getProperty('SHARED_SECRET');
    if (!secret || body.secret !== secret) {
      throw new Error('bad secret');
    }
    out = handle_(body);
    out.ok = true;
  } catch (err) {
    out = { ok: false, error: String(err && err.message ? err.message : err) };
  }
  return ContentService.createTextOutput(JSON.stringify(out)).setMimeType(
    ContentService.MimeType.JSON
  );
}

function listId_() {
  var props = PropertiesService.getScriptProperties();
  var saved = props.getProperty('LIST_ID');
  if (saved) {
    try {
      Tasks.Tasklists.get(saved);
      return saved;
    } catch (err) {
      // the list was deleted: look for it again or create it
    }
  }
  var lists = Tasks.Tasklists.list({ maxResults: 100 }).items || [];
  for (var i = 0; i < lists.length; i++) {
    if (lists[i].title === LIST_TITLE) {
      props.setProperty('LIST_ID', lists[i].id);
      return lists[i].id;
    }
  }
  var created = Tasks.Tasklists.insert({ title: LIST_TITLE });
  props.setProperty('LIST_ID', created.id);
  return created.id;
}

function dueToRfc_(iso) {
  return iso + 'T00:00:00.000Z';
}

function pick_(t) {
  return {
    id: t.id,
    title: t.title,
    notes: t.notes || '',
    due: t.due || null,
    status: t.status,
    completed: t.completed || null
  };
}

function handle_(body) {
  var list = listId_();
  switch (body.action) {
    case 'list':
      var tasks = [];
      var token = null;
      do {
        var page = Tasks.Tasks.list(list, {
          showCompleted: true,
          showHidden: true,
          maxResults: 100,
          pageToken: token
        });
        (page.items || []).forEach(function (t) {
          tasks.push(pick_(t));
        });
        token = page.nextPageToken;
      } while (token);
      return { tasks: tasks };
    case 'create':
      return {
        task: pick_(
          Tasks.Tasks.insert(
            { title: body.title, notes: body.notes, due: dueToRfc_(body.due) },
            list
          )
        )
      };
    case 'update':
      Tasks.Tasks.patch({ title: body.title, due: dueToRfc_(body.due) }, list, body.id);
      return {};
    case 'complete':
      var task = Tasks.Tasks.get(list, body.id);
      var notes = String(task.notes || '');
      if (notes.toLowerCase().indexOf(body.recordedWord) < 0) {
        notes += ' ' + body.recordedWord;
      }
      Tasks.Tasks.patch({ status: 'completed', notes: notes }, list, body.id);
      return {};
    case 'delete':
      Tasks.Tasks.remove(list, body.id);
      return {};
    default:
      throw new Error('unknown action');
  }
}
