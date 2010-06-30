## Copyright 2009 Laurent Bovet <laurent.bovet@windmaster.ch>
##                Jordi Puigsegur <jordi.puigsegur@gmail.com>
##
##  This file is part of WFrog
##
##  WFrog is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.


import smtplib
import logging
import logging.handlers
import string
import types
 
class mySMTPHandler(logging.handlers.SMTPHandler):
    """
    A customized handler class which sends an SMTP email for each
    logging event, and supports TLS smtp servers, like gmail
    """

    def __init__(self, mailhost, fromaddr, toaddrs, subject, credentials=None):
        """
        Initialize the handler.
 
        Initialize the instance with the from and to addresses and subject
        line of the email. To specify a non-standard SMTP port, use the
        (host, port) tuple format for the mailhost argument. To specify
        authentication credentials, supply a (username, password) tuple
        for the credentials argument. If TLS is required (gmail) it will
        be activated automatically
        """
        logging.handlers.SMTPHandler.__init__(self, mailhost, fromaddr, toaddrs, subject)
 
        # Python 2.5 SMTPHAndler object does not admit login credentials
        if type(credentials) == types.TupleType:
            self.username, self.password = credentials
        else:
            self.username = None


    def emit(self, record):
        """
        Emit a record.
 
        Format the record and send it to the specified addressees.
        """

        try:
            try:
                from email.utils import formatdate
            except ImportError:
                formatdate = self.date_time
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            string.join(self.toaddrs, ","),
                            self.getSubject(record),
                            formatdate(), msg)
            smtp.ehlo()
            if smtp.has_extn('STARTTLS'):
                smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

# Test mySMTPHandler
if __name__ == '__main__':

    MY_ACCOUNT = 'myAccount@gmail.com'
    MY_PASSWD = 'myPassword'
    handler = mySMTPHandler(('smtp.gmail.com', 587), MY_ACCOUNT, [MY_ACCOUNT], 
                             'Testing wfrog critical mail messages', 
                             (MY_ACCOUNT, MY_PASSWD))

    logger = logging.getLogger('wfrog_test')
    handler.setLevel(logging.CRITICAL)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


    print "Testing critical e-mail"
    logger.critical('This is a test ... you should be reading this inside a new email')
    



