# bonita-pysync
A custom python implementation of an LDAP synchronizer for Bonita BPM platform. Purely using REST APIs. 


### Note
This is an example implementation of how the Bonita REST API's could be used to import users from an LDAP source alongside some custom logic (profile, group, role creations etc.). 

Essentially the goal was to be able to run this script on a Bonita instance with ZERO setup (no users, roles, profiles, nothing), and get it into a state where we can start installing BDM and processes within seconds. 
It also serves as a reliable user importer if these groups are changed externally. By simply putting this script on a job an environment can be kept up to date without issue. 
