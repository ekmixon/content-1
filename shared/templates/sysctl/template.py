import ssg.utils


def preprocess(data, lang):
    data["sysctlid"] = ssg.utils.escape_id(data["sysctlvar"])
    if not data.get("sysctlval"):
        data["sysctlval"] = ""
    ipv6_flag = "I" if data["sysctlid"].find("ipv6") >= 0 else "P"
    data["flags"] = f"SR{ipv6_flag}"
    if "operation" not in data:
        data["operation"] = "equals"
    return data
