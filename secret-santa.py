#!/usr/bin/env python3

import random
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

if not (sys.version_info[0] >= 3):
    raise Exception("Python version 3.0 or greater required")

class Mailer(object):
    """Responsible for sending emails, managed an SMTP client"""
    def __init__(self, host, port, username, password=None, startls=False, dryrun=False):
        self.host = host
        self.port = port
        self.startls = startls,
        self.username = username
        self.password = password
        self.dryrun = dryrun
        self.client = None
        
    def _check_password(self):
        """Prompts for the password if it wasn't passed in the c'tor"""
        if self.password is None:
            import getpass
            self.password = getpass.getpass("Password for {0} ({1})".format(self.username, self.host))

    def connect(self):
        """Connects the SMTP client to the mail server"""
        self._check_password()
        if not self.dryrun:
            assert self.client is None
            self.client = smtplib.SMTP(self.host, self.port)
            self.client.ehlo()
            if self.startls:
                self.client.starttls()
                self.client.ehlo()
            self.client.login(self.username, self.password)


    def send(self, to, subject, text):
        """Sends an email using the (already connected) SMTP client"""
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(text))

        if not self.dryrun:
            assert self.client is not None
            self.client.sendmail(self.username, to, msg.as_string())
        else :
            print(text)

    def disconnect(self):
        """Disconnects the SMTP client from the mail server"""
        # Should be client.quit(), but that crashes...
        if not self.dryrun:
            assert self.client is not None
            self.client.close()
            
    def __enter__(self):
        self.connect()
        
    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()


class SantaException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Santa(object):
    """Represents a person who can act as a secret Santa to another person"""
    def __init__(self, name, email, exclusions = None):
        """Name is the person's name, email is their email address, and 
        exclusions (optional) is a list of the names of people who this person
        should not be santa to (spouses etc)"""
        if name is None:
            raise SantaException("Name is required")
        self.name = name
        if email is None:
            raise SantaException("Email is required")
        self.email = email
        self.exclusions = set()
        if not (exclusions is None):
            self.exclusions |= set(exclusions)
            
    def __str__(self):
        return self.name

class SantaAssignments(object):
    """Constructs the secret Santa assignments."""
    def __init__(self, santas, max_cpu = 10000):
        """Pseudo-randomly assigns a single secret Santa to every Santa, 
        subject to the constraints imposed by each Santa's 
        exclusions. If given, max_cpu bounds the CPU time which may be 
        spent finding a satisfactory assignment."""
        self._santas = santas
        self._max_cpu = max_cpu
        self._check()
        self._avoid_self_santa()
        self._assign()

    def _check(self):
        """Do some consistency checks on the Santas, throw a SantaException if 
        a problem is detected"""
        emails = set()
        names = set()
        for santa in self._santas:
            # check emails are unique
            if santa.email in emails:
                exit = True
                raise SantaException("Emails not unique: There are two (or more) Santas with address {0}".format(p.email))
            emails.add(santa.email)
            # check names are unique
            if santa.name in names: 
                exit = True
                raise SantaException("Names not unique: There are two (or more) Santas called {0}".format(p.name))
            names.add(santa.name)
        
        # check exclusions
        for santa in self._santas:
            for excl in santa.exclusions:
                if not (excl in names):
                    exit = True;
                    raise SantaException(
                        "Santa {0} has exclusion {1} who doesn't exist".format(santa.name, excl))

    def _avoid_self_santa(self):
        """Prevent Santas from being Santa to themsevles"""
        for santa in self._santas:
            santa.exclusions.add(santa.name)

    def _assign(self):
        """Assign a Santa to every other santa"""
        if self._max_cpu is None:
            def cpu_time():
                return 0
        else:
            import resource
            def cpu_time():
                return resource.getrusage(resource.RUSAGE_SELF)[0]
        start = cpu_time()
        while True:
            if start - cpu_time() > self._max_cpu:
                raise SantaException(
                    "Unable to find suitable assignments within allocated CPU time")
            recievers = [santa.name for santa in self._santas]
            random.shuffle(recievers);
            self.assignments = list(zip(self._santas, recievers))
            # Now check that the exclusion constraints are satisfied
            bad = False
            for santa, reciever in self.assignments:
                if reciever in santa.exclusions:
                    bad = True
            if not bad:
                break

    def _body(self, template, santa, reciever):
        return template.format(santa=santa.name, reciever=reciever)

    def email(self, mail_conf, template):
        with (mail_conf):
            for santa, reciever in self.assignments:
                mail_conf.send(santa.email, "Secret Santa", self._body(template, santa, reciever))

    def print_assignments(self):
        for santa, reciever in self.assignments:
            print(santa.name, "is santa to", reciever)
            
    def print_assignment_emails(self):
        for santa, reciever in self.assignments:
            print(body(santa, reciever))


if __name__ == '__main__':
    CONF = {}
    actions = {'print': lambda sa: sa.print_assignments(),
        'email_check': lambda sa: sa.email(CONF['MAIL_CONF'], CONF['EMAIL_CHECK']),
        'email': lambda sa: sa.email(CONF['MAIL_CONF'], CONF['EMAIL_ASSIGNMENT']) 
    }
    import argparse
    parser = argparse.ArgumentParser(description="Generates assignments for a 'secret santa'.")
    parser.add_argument('action', 
        metavar='ACTION', 
        type=str, 
        choices=list(actions.keys()),
        help="""The action/subcommand:
'print'         Generates assignments and prints them to the console.
'email_check'   Sends a preparatory email message to each of the santas, which 
                can be useful to confirm the email addresses are all correct.
'email'         Generates assignments and sends an email to each Santa 
                informing them who they're to be Santa to.""")
    parser.add_argument('conf_file', 
        metavar='CONFIG', 
        type=str, 
        help="A config file containing the Santa's details and email information")
    parser.add_argument('--dry-run', 
        dest="dryrun", 
        action="store_const", 
        const=True, 
        default=False, 
        help="Do everything except actually send the email")
    args = parser.parse_args()
    exec(compile(open(args.conf_file).read(), args.conf_file, 'exec'), {'Mailer': Mailer, 'Santa': Santa}, CONF)
    CONF['MAIL_CONF'].dryrun = args.dryrun
    actions[args.action](SantaAssignments(CONF['SANTAS']))

