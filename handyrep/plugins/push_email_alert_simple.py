# simple plugin for emailing
# push alerts to one specific email address

from plugins.handyrepplugin import HandyRepPlugin

import smtplib

from email.mime.text import MIMEText

class push_email_alert_simple(HandyRepPlugin):

    def run(self, alert_type, category, message):
        myconf = get_myconf()
        clustname = self.conf["handyrep"]["cluster_name"]

    msgtext = "HandyRep Server Alert:

Cluster: %s

Category: %s

Message: %s""" % (clustname, category, message,)

    msg = MIMEText(msgtext)
    if myconf["subject"]:
        subjtag = myconf["subject"]
    else:
        subjtag = "[HandyRepAlert]"

    msg["Subject"] = "%s: %s %s %s" % (subjtag, clustname, alert_type, category,)
    msg["From"] = myconf["email_from"]
    msg["To"] = myconf["email_to"]

    if self.is_true(myconf["use_ssl"]):
        sendit = smtplib.SMTP_SSL()
    else:
        sendit = smtplib.SMTP()

    if myconf["smtpport"]:
        smport = self.as_int(myconf["smtpport"])
    else:
        smport = 26

    try:
        sendit.connect(myconf["smtpserver"], smport)
    except:
        self.log("ALERT","Unable to connect to mail server",True)
        return self.rd(False, "Cannot connect to mail server")
    
    if myconf["smtpserver"] <> "localhost":
        try:
            sendit.ehlo()

            if self.is_true(myconf["use_tls"]):
                sendit.starttls()
                sendit.ehlo()

            sendit.login(myconf["username"], myconf["smtp_pass"])
        except:
            sendit.quit()
            self.log("ALERT","Unable to log in to mail server",True)
            return self.rd(False, "Cannot log in to mail server")

    try:
        sendit.sendmail(efrom, [eto,], msg.as_string())
        sendit.quit()
    except:
        self.log("ALERT","Cannot send mail via mail server",True)
        return self.rd(False, "Cannot send mail via mail server")

    return self.rd(True, "Alert mail sent")


    def test(self):
        # check for required configuration
        if self.failed(self.test_plugin_conf("push_email_alert_simple","email_to", "email_from", "smtpserver")):
            return self.rd(False, "plugin push_email_alert_simple is not correctly configured")
        else:
            return self.rd(True, "plugin passes")