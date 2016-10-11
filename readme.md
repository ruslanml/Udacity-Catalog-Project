#Udacity Catalog Project

This is a simple catalog app built with Python, Flask and SQLAlchemy. The app supports user authentication and authorization using OAuth 2.0 and Facebook Login API.
Logged in users can add categories and items, as well as edit, delete categories and items that they have created. Users who are not logged in can view the contents of the catalog but cannot make changes.

####Installation

1. Ensure you have git installed. To install on Mac, download and install from: http://git-scm.com/download/mac. To install on Windows, download and install from: http://git-scm.com/download/win.
2. Ensure you have Python installed. To install on Mac, download and install from: https://www.python.org/ftp/python/2.7.12/python-2.7.12-macosx10.6.pkg. To install on Windows, download and install from: https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi.
3. Download and install Virtual Box from https://www.virtualbox.org/wiki/Downloads.
4. Download and install Vagrant from https://www.vagrantup.com/downloads.
5. Open system's command line.
6. Change to the desired directory
  - Example: `cd ~/` for the main User 
3. Using Git, clone the Udacity VM configuration:
  - Run: `git clone https://github.com/udacity/fullstack-nanodegree-vm.git`
  - This will create a new directory titled *vagrant* that contains all of the necessary configurations to run this application.
4. Move to the *vagrant* folder by entering: `cd ~/vagrant/`
5. Clone the github repository by running the command below:
  - Run: `git clone https://github.com/ruslanml/Udacity-Catalog-Project.git`
  - This will create a directory inside the *vagrant* directory titled *catalog*.
6. Run Vagrant by entering: `vagrant up`
7. Log into Vagrant VM by entering: `vagrant ssh`
8. Move to *catalog* directory by entering: `cd /vagrant/catalog/`
9. Run the main project file, run: `python project.py`
10. View the app on your browser, go to: `http://0.0.0.0:5000/`