# DNS records for reaganleonardmusic.com — captured 2026-09-10, just before
# connecting the domain to the file-based hosting site.
#
# If Hostinger resets the zone during the switch, restore these in
# hPanel → Domains → reaganleonardmusic.com → DNS / Nameservers.
# Email is on Titan (not Hostinger's free email plan); these MX/TXT records
# are what keep reagan@reaganleonardmusic.com working.

| Type | Name | Value | Priority |
|---|---|---|---|
| MX | @ | mx1.titan.email | 10 |
| MX | @ | mx2.titan.email | 20 |
| TXT | @ | v=spf1 include:spf.titan.email ~all | |
| TXT | @ | brevo-code:4dc838b980d8b166363cbd53788ff4f8 | |
| TXT | @ | google-site-verification=awPYoSw1jNF2zBQLqRbEg-1oPDBE6iYoWOnKEHT0_J4 | |
| TXT | titan1._domainkey | v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCgWMEBJE/CvFxz14dFQ63yk4ku+gHukbDwqOidfAcoX1nspf1+h0zp19uRdlJBcnX5G1bM1dTPT1QJ+clw2O3t29di1wFHhKKift/3GBbmDBuKNbZzedep3GGgC+BXNkV8qXzTPj5n6cJCr8DHYIqVfoRIJZi9DL6KoPjJQQ+6GQIDAQAB | |
| TXT | _dmarc | v=DMARC1; p=none; rua=mailto:rua@dmarc.brevo.com | |
| CNAME | www | connect.hostinger.com (builder; will change to the hosting target after the switch) | |
| A | @ | 88.222.222.171 / 2.57.91.59 (builder; will change to the hosting IP after the switch) | |
| NS | @ | ns1.dns-parking.com, ns2.dns-parking.com | |
