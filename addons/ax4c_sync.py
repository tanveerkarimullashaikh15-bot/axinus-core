# patch: UI tells the Android app (if running inside it) to schedule task alarms
_a = "tasks=r.tasks||[];renderTasks();"
if _a in UI_BODY and "AXAND" not in UI_BODY:
    UI_BODY = UI_BODY.replace(_a, _a + "try{if(window.AXAND)AXAND.sync(JSON.stringify(tasks));}catch(e){}")
    if "API" in globals() and "build_old_js" in globals():
        _oj, _w = build_old_js(PAGE)
        UI_HTML = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>AXINUS</title></head><body>' + UI_BODY.replace("__OLD__", _oj) + '</body></html>'
    print("✅ android task-sync ON")
else: print("sync patch skipped (already applied or UI changed)")
