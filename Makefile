TAR=tar
#TAR=gtar

clean: accounts
	-rm *.tar
	-rm -r accounts_web accounts_backend
	-find accounts -name \*.pyc -exec rm {} \;
	-rm accounts/db.sqlite

web: clean accounts
	cp -r accounts accounts_web
	rm -r accounts_web/scripts/{auth_modules,create.py,process-changes.py,remind.py,test_modules}
	rm -r accounts_web/tests
	cp account_launcher.wsgi accounts_web
	$(TAR) cvf accounts_web.tar accounts_web
	rm -r accounts_web

backend: clean accounts
	cp -r accounts accounts_backend
	rm -r accounts_backend/{pages,static,templates,tests,web}
	cp -r standalone_scripts accounts_backend
	$(TAR) cvf accounts_backend.tar accounts_backend
	rm -r accounts_backend

database:
	python accounts -r
	python accounts -s import_passwd
	python accounts -s import_old_db

all: web backend
