# coding: utf-8
import sys
import traceback
import time
import glob
import os
import pyinotify
import datetime
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, TemplateError

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
TEMPLATES_DIR = os.path.join(PROJECT_DIR, 'templates')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'www')

class EventHandler(pyinotify.ProcessEvent):
    def process(self, event):
        name = os.path.basename(event.pathname)
        if event.path == os.path.join(TEMPLATES_DIR, "layout"):
            render_all()
        elif name.endswith(".html") and name[0] != '.':
            render(name)

    def process_IN_MODIFY(self, event):
        # print "modified:", event.pathname
        self.process(event)

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

def monitor():
    wm = pyinotify.WatchManager() # Watch Manager
    handler = EventHandler()
    notifier = pyinotify.Notifier(wm, handler, timeout=100)
    wdd = wm.add_watch(TEMPLATES_DIR, pyinotify.ALL_EVENTS, auto_add=True, rec=True)
    print "Monitoring for changes in {}. Exit with Ctrl-C".format(TEMPLATES_DIR)
    notifier.loop()

def render(template_name):
    print "Rendering {}".format(template_name)
    start = time.time()
    template = env.get_template(template_name)
    simplename = os.path.splitext(template_name)[0]
    context = {"bodyclass": simplename}

    function_name = "template_" + simplename
    function = globals().get(function_name)
    if function is not None:
        print "calling template function {} for template {}".format(function_name, template_name)
        newdata = function()
        try:
            context = dict(context.items() + newdata.items())
        except AttributeError:
            print ("===> Warning: template functions should return "
                   "dict-like objects: {} returned {}").format(function_name, newdata.__class__.__name__)

    with open(os.path.join(OUTPUT_DIR, template_name), 'w') as f:
        try:
            template.stream(**context).dump(f, 'utf-8')
        except Exception, e:
            print "Error rendering {}: {}".format(template_name, e)
            f.write("<pre>\n")
            traceback.print_exc(file=f)
            f.write("\n</pre>")
        f.flush()

    elapsed = (time.time() - start) * 1000
    print "  done in {:.2f} ms".format(elapsed)

def render_all():
    print "Re-rendering all files"
    for x in glob.glob(os.path.join(TEMPLATES_DIR, '*.html')):
        render(os.path.basename(x))

def main():
    render_all()
    monitor()

if __name__ == "__main__":
    main()
