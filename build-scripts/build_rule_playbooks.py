#!/usr/bin/python3

import argparse
import ssg.playbook_builder
import os


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input-dir",
        help="Input directory that contains all Ansible remediations "
        "snippets for the product we are building. "
        "e.g. ~/scap-security-guide/build/fedora/fixes/ansible. "
        "If --input-dir is not specified, it is derived from --ssg-root."
    )
    p.add_argument(
        "--output-dir",
        help="Output directory to which the rule-based Ansible playbooks "
        "will be generated. "
        "e.g. ~/scap-security-guide/build/fedora/playbooks. "
        "If --output-dir is not specified, it is derived from --ssg-root."
    )
    p.add_argument(
        "--resolved-rules-dir",
        help="Directory that contains preprocessed rules in YAML format "
        "eg. ~/scap-security-guide/build/fedora/rules. "
        "If --resolved-rules-dir is not specified, it is derived from "
        "--ssg-root."
    )
    p.add_argument(
        "--resolved-profiles-dir",
        help="Directory that contains preprocessed profiles in YAML format "
        "eg. ~/scap-security-guide/build/fedora/profiles. "
        "If --resolved-profiles-dir is not specified, it is derived from "
        "--ssg-root."
    )
    p.add_argument(
        "--ssg-root", required=True,
        help="Directory containing the source tree. "
        "e.g. ~/scap-security-guide/"
    )
    p.add_argument(
        "--product", required=True,
        help="ID of the product for which we are building Playbooks. "
        "e.g.: 'fedora'"
    )
    p.add_argument(
        "--profile",
        help="Generate Playbooks only for given Profile ID. Accepts profile "
        "ID in the short form, eg. 'ospp'. If not specified, Playbooks are "
        "built for all available profiles."
    )
    p.add_argument(
        "--rule",
        help="Generate Ansible Playbooks only for given rule specified by "
             "a shortened Rule ID, eg. 'package_sendmail_removed'. "
             "If not specified, Playbooks are built for every rule."
    )
    return p.parse_args()


def main():
    args = parse_args()
    product_yaml = os.path.join(args.ssg_root, "products", args.product, "product.yml")
    input_dir = args.input_dir or os.path.join(
        args.ssg_root, "build", args.product, "fixes", "ansible"
    )

    output_dir = args.output_dir or os.path.join(
        args.ssg_root, "build", args.product, "playbooks"
    )

    resolved_rules_dir = args.resolved_rules_dir or os.path.join(
        args.ssg_root, "build", args.product, "rules"
    )

    resolved_profiles_dir = args.resolved_profiles_dir or os.path.join(
        args.ssg_root, "build", args.product, "profiles"
    )

    playbook_builder = ssg.playbook_builder.PlaybookBuilder(
        product_yaml, input_dir, output_dir, resolved_rules_dir, resolved_profiles_dir
    )
    playbook_builder.build(args.profile, args.rule)


if __name__ == "__main__":
    main()
