from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    description: str
    command: str
    timeout: int = 1800


MODULES: list[ModuleSpec] = [
    ModuleSpec("index", "Result index header", "bash modules/index.sh {url}"),
    ModuleSpec("dnscan", "DNS enumeration", "bash modules/dnscan.sh {url}", 600),
    ModuleSpec("clickjacking", "Clickjacking probe", "python modules/clickjacking {url}", 300),
    ModuleSpec("corstest", "CORS misconfig test", "python modules/corstest {url}", 600),
    ModuleSpec("firewall", "WAF detection", "bash modules/firewall.sh {url}", 300),
    ModuleSpec("davtest", "WebDAV testing", "bash modules/davtest.sh {url}", 600),
    ModuleSpec("robots", "robots.txt analysis", "bash modules/robots.sh {url}", 120),
    ModuleSpec("subdomains", "Subdomain enumeration", "bash modules/subdomains.sh {url}", 1800),
    ModuleSpec("dirb", "Directory brute force", "bash modules/dirb.sh {url}", 1800),
    ModuleSpec("js-finder", "JS / link finder", "bash modules/js-finder.sh {url}", 900),
    ModuleSpec("subtake", "Subdomain takeover check", "bash modules/subtake.sh {url}", 600),
    ModuleSpec("sub_title_cname", "Subdomain titles + CNAMEs", "bash modules/sub_title_cname.sh {url}", 900),
    ModuleSpec("sub_ip_server", "Subdomain IPs + servers", "bash modules/sub_ip_server.sh {url}", 900),
    ModuleSpec("whois", "WHOIS lookup", "bash modules/whois.sh {url}", 120),
    ModuleSpec("shcheck", "Security headers check", "bash modules/shcheck.sh {url}", 300),
    ModuleSpec("wappy", "Tech fingerprint (Wappalyzer)", "bash modules/wappy.sh {url}", 300),
    ModuleSpec("gather_urls", "URL gathering", "bash modules/gather_urls.sh {url}", 1800),
    ModuleSpec("gf_patterns", "GF pattern triage", "bash modules/gf_patterns.sh {url}", 900),
]


def get_module(name: str) -> ModuleSpec | None:
    for m in MODULES:
        if m.name == name:
            return m
    return None
