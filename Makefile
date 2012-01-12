TAR=tar
#TAR=gtar
CHROOT=/home/www
CHROOT_HTDOCS=/apache/htdocs
WEBTARGET=${CHROOT}${CHROOT_HTDOCS}

clean: accounts
	-@rm *.tar
	-@rm -r accounts_web accounts_backend
	-@find accounts -name \*.pyc -exec rm {} \;
	-@rm accounts/db.sqlite

wsgi: account_launcher.wsgi.base
	sed s@HTDOCS@${CHROOT_HTDOCS}@ account_launcher.wsgi.base > account_launcher.wsgi

web: wsgi clean accounts
	cp -r accounts accounts_web
	rm -r accounts_web/scripts/{auth_modules,create.py,process-changes.py,remind.py,test_modules}
	rm -r accounts_web/tests
	#cp account_launcher.wsgi accounts_web
	$(TAR) cvf accounts_web.tar accounts_web account_launcher.wsgi
	rm -r accounts_web

install_web: web
	$(TAR) xvf accounts_web.tar -C ${WEBTARGET}

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
