#! /usr/bin/python3.5

# ------------------------------------
# Bonita BPM Environment Synchronizer
# Does the following:
# - Checks for required groups UoA, Member and creates them if they don't exist
# - Checks for required roles CSRSupervisors, Developers, MPD, Member, PPC, QA. Each is created if not present
# - Checks for profiles BasicAppAccess, CSRStaff and creates them if not present
# - Gets 'User' profile details
# - Assigns previously created roles to required profiles
# - Gets all users from groups specified in 'groups.conf'
# - Checks if each user is in bonita
# - Creates user if they don't exist
# - Updates their contact information with latest ldap data
# - Adds user to group 'UOA'
# - Adds user to role 'Member'
# - Detect + add appropriate dev + qa roles
# - Detect + add to PPC roles
# - Detect + add to Supervisor roles
# - Detect + add to MPD roles
# - Backs up all processed Bonita ID's into 'bonita-ids.txt'
#
# Author: Max Tuzzolino-Smith
# ------------------------------------

import subprocess
import requests
import json

# ------------------------------------
# Constant/Config Variables
# ------------------------------------

ldap_host = "ldap-vip.auckland.ac.nz"
ldap_user = "cn=user,ou=webapps,ou=ec,o=uoa"
ldap_pass = "pass"

# API configuration
url = "http://localhost:8080/bonita"
admin = 'mtuz243'
headers = {
    'REMOTE_USER': admin,
    'Cookie': 'BOS_locale=en'
}

# Profile role lists
user_roles = []
app_access_roles = []
csr_staff_roles = []

# Diagnostics
rest_calls = 0

# Get admin bonita id
admin_id = requests.get("{bonita_url}/API/identity/user?p=0&c=100&f=userName={admin}".format(
    bonita_url=url, admin=admin), headers=headers).json()[0]['id']
rest_calls += 1


# ------------------------------------
# Methods
# ------------------------------------

# Bare minimum required to process a user
def empty():
    if upi and mail and firstName:
        return False
    else:
        return True


# ------------------------------------
# Import environment
# ------------------------------------
print("# ------------------------------------\n"
      "# BonitaBPM Environment Synchronize\n"
      "# Author: Max Tuzzolino-Smith\n"
      "# ------------------------------------\n")

# ----------
# Groups
# - Groups
# - UoA
# ----------

print("--> Processing groups")

# Groups
try:
    bonita_groups_gid = requests.get("{bonita_url}/API/identity/group?p=0&c=100&f=name=Groups".format(
        bonita_url=url), headers=headers).json()[0]['id']
    rest_calls += 1

    print("'Groups' group detected")
except IndexError:
    # Does not exist; create it
    groupPayload = {
        'name': 'Groups',
        'displayName': 'Groups',
        'description': 'Container for selected NetAccount groups'
    }

    print("Creating 'Groups'")

    # Create and return bonita_groups_gid
    bonita_groups_gid = requests.post("{bonita_url}/API/identity/group".format(bonita_url=url),
                                      data=json.dumps(groupPayload), headers=headers).json()['id']
    rest_calls += 1

    print("'Groups' group created with id {}".format(bonita_groups_gid))

# UoA
try:
    uoa_gid = requests.get("{bonita_url}/API/identity/group?p=0&c=100&f=name=UoA".format(bonita_url=url),
                           headers=headers).json()[0]['id']
    rest_calls += 1

    print("'UoA' group detected")
except IndexError:

    print("Creating 'UoA' group")

    # Create UoA group
    groupPayload = {
        'name': 'UoA',
        'displayName': 'UoA',
        'description': 'Root of University of Auckland org structure'
    }

    # Create and return bonita_groups_gid
    uoa_gid = requests.post("{bonita_url}/API/identity/group".format(bonita_url=url),
                            data=json.dumps(groupPayload), headers=headers).json()['id']
    rest_calls += 1

    print("'UoA' group created with id {}".format(uoa_gid))

# ----------
# Roles
# - CSRSupervisors
# - Developers
# - MPD
# - Member
# - PPC
# - QA
# ----------

print("--> Processing roles")

# Member
try:
    uoa_mem_rid = requests.get("{bonita_url}/API/identity/role?p=0&c=100&f=name=member".format(bonita_url=url),
                               headers=headers).json()[0]['id']
    rest_calls += 1

    print("'Member' role detected")
except IndexError:
    print("Creating 'member' role")

    rolePayload = {
        'description': 'Member of any group. Can be used to reference all people '
                       'in the organization since everyone is a member of some group (typically org unit)',
        'name': 'member',
        'displayName': 'Member',
    }

    # Create and return uoa_mem_rid
    uoa_mem_rid = requests.post("{bonita_url}/API/identity/role".format(bonita_url=url),
                                data=json.dumps(rolePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'Member' role created with id {}".format(uoa_mem_rid))

# Add member role id to BasicAppAccess list
app_access_roles.append(uoa_mem_rid)

# Add admin user to 'Member' role (for BasicAppAccess privileges)
requests.post("{bonita_url}/API/identity/membership".format(bonita_url=url),
              headers=headers, data=json.dumps(
        {
            'user_id': admin_id,
            'group_id': uoa_gid,
            'role_id': uoa_mem_rid
        }))
rest_calls += 1

# Developers
try:
    dev_rid = requests.get("{bonita_url}/API/identity/role?p=0&c=100&f=name=Developers".format(bonita_url=url),
                           headers=headers).json()[0]['id']
    rest_calls += 1

    print("'Developer' role detected")
except IndexError:
    print("Creating 'Developer' role")

    rolePayload = {
        'description': 'Members of the Team',
        'name': 'Developers',
        'displayName': 'Developers',
    }

    # Create and return dev_rid
    dev_rid = requests.post("{bonita_url}/API/identity/role".format(bonita_url=url),
                            data=json.dumps(rolePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'Developers' role created with id {}".format(dev_rid))

# Add to user profile
user_roles.append(dev_rid)

# QA
try:
    qa_rid = requests.get("{bonita_url}/API/identity/role?p=0&c=100&f=name=QA".format(bonita_url=url),
                          headers=headers).json()[0]['id']
    rest_calls += 1

    print("'QA' role detected")
except IndexError:
    print("Creating 'QA' role")

    rolePayload = {
        'description': 'Members of QA Team',
        'name': 'QA',
        'displayName': 'QA',
    }

    # Create and return dev_rid
    qa_rid = requests.post("{bonita_url}/API/identity/role".format(bonita_url=url),
                           data=json.dumps(rolePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'QA' role created with id {}".format(qa_rid))

# Add to user profile
user_roles.append(qa_rid)

# MPD
try:
    mpd_rid = requests.get("{bonita_url}/API/identity/role?p=0&c=100&f=name=MPD".format(
        bonita_url=url), headers=headers).json()[0]['id']
    rest_calls += 1

    print("'MPD' role detected")
except IndexError:
    print("Creating 'MPD' role")

    rolePayload = {
        'description': 'ECSR MPD role',
        'name': 'MPD',
        'displayName': 'MPD',
    }

    # Create and return dev_rid
    mpd_rid = requests.post("{bonita_url}/API/identity/role".format(bonita_url=url),
                            data=json.dumps(rolePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'MPD' role created with id {}".format(mpd_rid))

# Add to profile list(s)
csr_staff_roles.append(mpd_rid)
user_roles.append(mpd_rid)

# Supervisors
try:
    supervisor_rid = requests.get("{bonita_url}/API/identity/role?p=0&c=100&f=name=CSRSupervisors".format(
        bonita_url=url), headers=headers).json()[0]['id']
    rest_calls += 1

    print("'CSRSupervisors' role detected")
except IndexError:
    print("Creating 'CSRSupervisors' role")

    rolePayload = {
        'description': 'ECSR supervisor role',
        'name': 'CSRSupervisors',
        'displayName': 'CSRSupervisors',
    }

    # Create and return dev_rid
    supervisor_rid = requests.post("{bonita_url}/API/identity/role".format(bonita_url=url),
                                   data=json.dumps(rolePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'CSRSupervisors' role created with id {}".format(supervisor_rid))

# Add to profile list(s)
csr_staff_roles.append(supervisor_rid)

# PPC
try:
    ppc_rid = requests.get("{bonita_url}/API/identity/role?p=0&c=100&f=name=PPC".format(
        bonita_url=url), headers=headers).json()[0]['id']
    rest_calls += 1

    print("'PPC' role detected")
except IndexError:
    print("Creating 'PPC' role")

    rolePayload = {
        'description': 'ECSR PPC role',
        'name': 'PPC',
        'displayName': 'PPC',
    }

    # Create and return dev_rid
    ppc_rid = requests.post("{bonita_url}/API/identity/role".format(bonita_url=url),
                            data=json.dumps(rolePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'PPC' role created with id {}".format(ppc_rid))

# Add to profile list(s)
csr_staff_roles.append(ppc_rid)
user_roles.append(ppc_rid)

# ----------
# Profiles
# - User
# - BasicAppAccess
# - CSRStaff
# ----------

print("--> Processing profiles")

# User (should exist by default on Bonita first startup)
user_profile_id = requests.get("{bonita_url}/API/portal/profile?p=0&c=100&f=name=User".format(
    bonita_url=url), headers=headers).json()[0]['id']
rest_calls += 1

print("----> Assigning roles to User profile")

# Assign roles to User profile
for role_id in user_roles:
    roleMemberPayload = {
        'profile_id': user_profile_id,
        'member_type': 'ROLE',
        'role_id': role_id
    }

    requests.post("{bonita_url}/API/portal/profileMember".format(bonita_url=url),
                  data=json.dumps(roleMemberPayload), headers=headers)
    rest_calls += 1

# BasicAppAccess
try:
    app_access_id = requests.get("{bonita_url}/API/portal/profile?p=0&c=100&f=name=BasicAppAccess".format(
        bonita_url=url), headers=headers).json()[0]['id']
    rest_calls += 1

    print("'BasicAppAccess' profile detected")
except IndexError:
    print("Creating 'BasicAppAccess' profile")

    profilePayload = {
        'name': 'BasicAppAccess',
        'description': 'This profile is used for accessing public REST API '
                       'extensions and application navigation endpoints.'
    }

    # Create and return app_access_id
    app_access_id = requests.post("{bonita_url}/API/portal/profile".format(bonita_url=url),
                                  data=json.dumps(profilePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'BasicAppAccess' profile created with id {}".format(app_access_id))

print("----> Assigning roles to BasicAppAccess profile")

# Assign roles to BasicAppAccess profile
for role_id in app_access_roles:
    roleMemberPayload = {
        'profile_id': app_access_id,
        'member_type': 'ROLE',
        'role_id': role_id
    }

    requests.post("{bonita_url}/API/portal/profileMember".format(bonita_url=url),
                  data=json.dumps(roleMemberPayload), headers=headers)
    rest_calls += 1

# CSRStaff
try:
    csr_staff_id = requests.get("{bonita_url}/API/portal/profile?p=0&c=100&f=name=CSRStaff".format(
        bonita_url=url), headers=headers).json()[0]['id']
    rest_calls += 1

    print("'CSRStaff' profile detected")
except IndexError:
    print("Creating 'CSRStaff' profile")

    profilePayload = {
        'name': 'CSRStaff',
        'description': 'Everyone involved in the CSR Process.'
    }

    # Create and return app_access_id
    csr_staff_id = requests.post("{bonita_url}/API/portal/profile".format(bonita_url=url),
                                 data=json.dumps(profilePayload), headers=headers).json()['id']
    rest_calls += 1

    print("'CSRStaff' profile created with id {}".format(csr_staff_id))

print("----> Assigning roles to CSRStaff profile")

# Assign roles to CSRStaff profile
for role_id in csr_staff_roles:
    roleMemberPayload = {
        'profile_id': csr_staff_id,
        'member_type': 'ROLE',
        'role_id': role_id
    }

    requests.post("{bonita_url}/API/portal/profileMember".format(bonita_url=url),
                  data=json.dumps(roleMemberPayload), headers=headers)
    rest_calls += 1

# ------------------------------------
# LDAP call (get users)
# ------------------------------------

print("--> Processing users")

# Read all the groups specified
groups = [line.rstrip('\n') for line in open('groups.conf')]

# Initiate list of users
users = []

for group in groups:
    users.extend(subprocess.Popen(
        "ldapsearch -ZZ -h {ldaphost} -x -D {ldapuser} -w $(echo {ldappass} | base64 -di) "
        "-b ou=ec_users,dc=ec,dc=auckland,dc=ac,dc=nz \""
        "(groupMembership=cn={ldapgroup},ou=ec_group,dc=ec,dc=auckland,dc=ac,dc=nz)\"".format(
            ldaphost=ldap_host,
            ldapuser=ldap_user,
            ldappass=ldap_pass,
            ldapgroup=group),
        shell=True,
        stdout=subprocess.PIPE).stdout.read().decode('ascii').split("dn: "))

print("Importing users from groups: {}".format(groups))

# ------------------------------------
# User logic
# ------------------------------------

# Iterate over user entries in group
for user in users:

    # Reset person details
    upi = ""
    mail = ""
    firstName = ""
    lastName = "-"
    personalTitle = ""

    # Group filters for differing logic
    api_team = False
    ppc_user = False
    supervisor = False
    mpd = False

    # Pull relevant user information
    for line in user.split('\n'):
        if "uid: " in line:
            upi = line.split(': ')[1]
        elif "mail: " in line:
            mail = line.split(': ')[1]
        elif "givenName: " in line:
            firstName = line.split(': ')[1]
        elif "sn: " in line:
            lastName = line.split(': ')[1]
        elif "personalTitle: " in line:
            personalTitle = line.split(': ')[1]
        elif "cn=api-team.its" in line:
            # Add to Developer and QA roles
            api_team = True
        elif "cn=ecsr-ppc.fmhs" in line:
            ppc_user = True
        elif "cn=ecsr-supervisors.fmhs" in line:
            supervisor = True
        elif "cn=ecsr-mpd.fmhs" in line:
            mpd = True

    # Only continue if all correct values are found
    if not empty():
        # Try fetch user information
        try:
            # Fetch bonita_id from our REST API extension
            bonita_id = requests.get(
                "{bonita_url}/API/identity/user?p=0&c=100&f=userName={username}".format(bonita_url=url, username=upi),
                headers=headers).json()[0]['id']
            rest_calls += 1

        except IndexError:
            # User doesn't exist; create them
            print("Creating user {}".format(upi))

            # Construct user creation payload
            userPayload = {
                'userName': upi,
                'password': 'bpm',
                'password_confirm': 'bpm',
                'firstname': firstName,
                'lastname': lastName,
                'title': personalTitle,
                'enabled': 'true'
            }

            # Create user and fetch bonita_id
            bonita_id = requests.post("{bonita_url}/API/identity/user".format(bonita_url=url),
                                      data=json.dumps(userPayload), headers=headers).json()['id']
            rest_calls += 1

            print("User {} created successfully with bonita identifier: {}".format(upi, bonita_id))

        # Construct contact payload
        contactPayload = {'email': mail}

        # Add email to users personal contact information
        requests.put(
            "{bonita_url}/API/identity/professionalcontactdata/{bonita_id}".format(bonita_url=url,
                                                                                   bonita_id=bonita_id),
            data=json.dumps(contactPayload), headers=headers)
        rest_calls += 1

        # Construct member payload
        memberPayload = {
            'user_id': bonita_id,
            'group_id': uoa_gid,
            'role_id': uoa_mem_rid
        }

        # Add user to group 'UOA' and set their role to 'Member"
        requests.post("{bonita_url}/API/identity/membership".format(bonita_url=url),
                      data=json.dumps(memberPayload), headers=headers)
        rest_calls += 1

        # Add to additional developer and qa roles if user is apart of core api-team
        if api_team:
            # Construct payloads
            devPayload = {
                'user_id': bonita_id,
                'group_id': bonita_groups_gid,
                'role_id': dev_rid
            }

            qaPayload = {
                'user_id': bonita_id,
                'group_id': bonita_groups_gid,
                'role_id': qa_rid
            }

            # Add user to Dev + QA roles in Bonita (for portal access)
            requests.post("{bonita_url}/API/identity/membership".format(bonita_url=url),
                          data=json.dumps(devPayload), headers=headers)
            rest_calls += 1

            requests.post("{bonita_url}/API/identity/membership".format(bonita_url=url),
                          data=json.dumps(qaPayload), headers=headers)
            rest_calls += 1

            print("User {} detected as Api-team member. Assigning DEV + QA membership.".format(upi))

        # Add to additional PPC user role if user is an ECSR ppc user
        if ppc_user:
            # Construct ppc payload
            ppcPayload = {
                'user_id': bonita_id,
                'group_id': bonita_groups_gid,
                'role_id': ppc_rid
            }

            # Add user to ppc role in bonita
            requests.post("{bonita_url}/API/identity/membership".format(bonita_url=url),
                          data=json.dumps(ppcPayload), headers=headers)
            rest_calls += 1

            print("User {} detected as PPC user. Assigning PPC membership.".format(upi))

        # Add to additional supervisor role if user is an ECSR supervisor
        if supervisor:
            # Construct supervisor payload
            supervisorPayload = {
                'user_id': bonita_id,
                'group_id': bonita_groups_gid,
                'role_id': supervisor_rid
            }

            # Add user to supervisor role in bonita
            requests.post("{bonita_url}/API/identity/membership".format(bonita_url=url),
                          data=json.dumps(supervisorPayload), headers=headers)
            rest_calls += 1

            print("User {} detected as CSR Supervisor. Assigning CSRSupervisor membership.".format(upi))

        # Add to MPD role if user is a MPD user
        if mpd:
            # Construct mpd payload
            mpdPayload = {
                'user_id': bonita_id,
                'group_id': bonita_groups_gid,
                'role_id': mpd_rid
            }

            # Add user to mpd role in bonita
            requests.post("{bonita_url}/API/identity/membership".format(bonita_url=url),
                          data=json.dumps(mpdPayload), headers=headers)
            rest_calls += 1

            # Placeholder code for when users are exported into bpmusers group
            print("User {} detected as MPD user. Assigning MPD membership.".format(upi))

        # Output info
        print("Imported successfully [ UPI: {}, Email: {}, Firstname: {}, Lastname: {}, Bonita ID: {}]".format(
            upi, mail, firstName, lastName, bonita_id))

        # Write bonita_ids to a file (useful in case something goes wrong)
        with open('bonita-ids.txt', 'a') as out:
            out.write("{}\n".format(bonita_id))

print("Environment builder complete. {} REST API calls were needed to build the environment".format(rest_calls))
