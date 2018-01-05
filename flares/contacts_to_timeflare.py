"""
Takes a list of atomic contacts as input and generates a json representing a temporal flare
which can be visualized using flareplots.
"""

def parse_contacts(contact_file):
    """
    Parses the contact file and returns it a list of atomic contacts. Atom strings are
    converted to tuples by splitting on ":".

    Parameters
    ----------
    contact_file: file
        Contact-file generated by dynamic_contacts.py

    Returns
    -------
    list of tuples
        e.g. [("0", "hbbb", ("A", "ARG", "4", "H"), ("A", "PHE", "22", "O")), (..) ]
    """
    def parse_atom(atom_str):
        atom_tokens = atom_str.split(":")
        return tuple(atom_tokens)

    ret = []
    for line in contact_file:
        line = line.strip()
        if not line:
            continue

        tokens = line.split("\t")
        if not len(tokens) in range(4, 7):
            raise AssertionError("Invalid interaction line: '"+line+"'")

        tokens[2] = parse_atom(tokens[2])
        tokens[3] = parse_atom(tokens[3])
        if len(tokens) >= 5:
            tokens[4] = parse_atom(tokens[4])
        if len(tokens) == 6:
            tokens[5] = parse_atom(tokens[5])
        ret.append(tuple(tokens))

    contact_file.close()

    return ret


def create_graph(contacts):
    ret = {
        "edges": []
    }

    # Strip atom3, atom4, atom names and chain ID if only 1 chain present
    unique_chains = set([c[2][0] for c in contacts] + [c[3][0] for c in contacts])
    if len(unique_chains) == 1:
        contacts = [(c[0], c[1], c[2][1:3], c[3][1:3]) for c in contacts]
    else:
        contacts = [(c[0], c[1], c[2][0:3], c[3][0:3]) for c in contacts]

    resi_edges = {}
    for contact in contacts:
        # Compose a key for atom1 and atom2 that ignores the order of residues
        a1_key = ":".join(contact[2][0:3])
        a2_key = ":".join(contact[3][0:3])
        if a1_key > a2_key:
            a1_key, a2_key = a2_key, a1_key
        contact_key = a1_key + a2_key

        # Create contact_key if it doesn't exist
        if not contact_key in resi_edges:
            edge = {"name1": a1_key, "name2": a2_key, "frames": []}
            resi_edges[contact_key] = edge
            ret["edges"].append(edge)

        resi_edges[contact_key]["frames"].append(int(contact[0]))

    # Sort edge frames and ensure that there are no duplicates
    for e in ret["edges"]:
        e["frames"] = sorted(set(e["frames"]))

    return ret


if __name__ == "__main__":
    import argparse as ap
    parser = ap.ArgumentParser(description=__doc__)
    optional = parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    parser._action_groups.append(optional)  # added this line

    required.add_argument('--input',
                          required=True,
                          type=ap.FileType('r'),
                          help='A multi-frame contact-file generated by dynamic_contact.py')
    required.add_argument('--output',
                          required=True,
                          type=ap.FileType('w'),
                          help='The json file to write flare to')

    optional.add_argument('--pdb',
                          required=False,
                          help='PDB file used for full sequence and secondary structure')
    optional.add_argument('--itype',
                          required=False,
                          default="hbss",
                          type=str,
                          help='Interaction types to include (comma separated list)')

    args = parser.parse_args()

    contacts = parse_contacts(args.input)
    graph = create_graph(contacts)

    import json
    args.output.write(json.dumps(graph, indent=2))
    args.output.close()
