@echo off
cd /d "%~dp0"
python -c "import sqlite3; c=sqlite3.connect(r'database\content_script.sqlite'); tables=['sources','viral_hooks','short_form_scripts','ctas','before_after_patterns','product_demo_patterns','testimonial_patterns']; [print(t, c.execute('select count(*) from '+t).fetchone()[0]) for t in tables]"
pause
