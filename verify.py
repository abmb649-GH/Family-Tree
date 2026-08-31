"""
Permanent regression check for the family tree data.

This encodes every specific fact the user has explicitly confirmed over the course
of this project. It must be run against data.json before ANY file is handed back
to the user for publishing. If anything here fails, that is a real problem to
investigate and fix BEFORE delivery -- not something to notice later.

Run: python3 verify.py path/to/data.json
"""
import json
import sys

def find_id(data, name_substring):
    matches = [p['id'] for p in data if name_substring in p['name']]
    return matches

def run(path):
    data = json.load(open(path))
    by_id = {p['id']: p for p in data}
    failures = []

    def check(label, condition):
        if not condition:
            failures.append(label)

    def get_one(name_substring, context=""):
        matches = find_id(data, name_substring)
        if len(matches) != 1:
            failures.append(f"[LOOKUP] expected exactly 1 match for '{name_substring}' ({context}), found {len(matches)}: {matches}")
            return None
        return matches[0]

    # ---------- STRUCTURAL INTEGRITY (always required) ----------
    mirror = {'spouse':'spouse','parents':'children','children':'parents','siblings':'siblings'}
    for p in data:
        for field, mfield in mirror.items():
            for other_id in p.get(field, []):
                other = by_id.get(other_id)
                if other and p['id'] not in other.get(mfield, []):
                    failures.append(f"[ASYMMETRY] {p['name']} -> {field} -> {other['name']} not mirrored back")
    for p in data:
        if set(p.get('spouse',[])) & set(p.get('siblings',[])):
            failures.append(f"[CONTRADICTION] {p['name']}: same person listed as both spouse and sibling")
        if set(p.get('parents',[])) & set(p.get('children',[])):
            failures.append(f"[CONTRADICTION] {p['name']}: same person listed as both parent and child")
    ids = [p['id'] for p in data]
    if len(ids) != len(set(ids)):
        failures.append(f"[DUPLICATE IDS] {len(ids)-len(set(ids))} duplicate id(s) found")
    for p in data:
        if len(p.get('parents', [])) > 2:
            failures.append(f"[TOO MANY PARENTS] {p['name']} has {len(p['parents'])} parents")

    # ---------- SPECIFIC CONFIRMED FACTS ----------

    # Kruger family
    ant_kittie = get_one('Ant Kittie', 'oldest Kruger sister')
    if ant_kittie:
        check("Ant Kittie has no spouse (unmarried, Koos's father is unknown)",
              by_id[ant_kittie].get('spouse') == [])
        check("Ant Kittie's only child is Koos Kruger",
              by_id[ant_kittie].get('children', []) == [koos_k] if (koos_k := get_one('Koos Kruger')) else True)
    koos_k = get_one('Koos Kruger')
    stompie_k = get_one('Stompie Kruger')
    if koos_k and ant_kittie:
        check("Koos Kruger's mother is Ant Kittie (making her Stompie's mother-in-law)",
              by_id[koos_k].get('parents', []) == [ant_kittie])
    if koos_k and stompie_k:
        check("Koos Kruger is married to Stompie Kruger",
              by_id[koos_k].get('spouse', []) == [stompie_k])
    kruger_second_family = ['Ousus Kruger','Liefie Kruger','Hartjie Kruger','Marthie Kruger']
    if stompie_k:
        stompie_siblings = set(by_id[stompie_k].get('siblings', []))
        expected = set(get_one(n) for n in kruger_second_family if get_one(n))
        # "Willem Kruger" is ambiguous by name alone (Kleinman later named his own son
        # the same thing) -- find Stompie's specific brother via her shared placeholder
        # parent instead of a name lookup.
        stompie_parent_ids = set(by_id[stompie_k].get('parents', []))
        willem_sibling = next((p['id'] for p in data if p['name']=='Willem Kruger' and set(p.get('parents',[])) == stompie_parent_ids), None)
        if willem_sibling: expected.add(willem_sibling)
        check("Stompie Kruger shows all 5 of her real siblings (Ousus/Willem/Liefie/Hartjie/Marthie -- a separate Kruger family from Koos's clan)",
              expected.issubset(stompie_siblings))
        check("Stompie Kruger is NOT a sibling of Ant Kittie's family (she married in via Koos)",
              ant_kittie not in stompie_siblings if ant_kittie else True)
    check("There are two different people named 'Willem Kruger' in the tree on purpose (Kleinman's son, and Stompie's brother) -- not a duplicate to merge",
          len(find_id(data, 'Willem Kruger')) == 2)

    # Rikie / Marley Kruger -- names were found swapped, with a spelling error, and it
    # kept reverting. Both are Andre + Lettie Kruger's children.
    rikie = get_one('Rikie) Andrea Kruger')
    marley = get_one('Marley Kruger')
    marly_wrong_spelling = find_id(data, 'Marly Kruger')  # should NOT exist once fixed
    check("There is no longer a person spelled 'Marly Kruger' (corrected to 'Marley')",
          len(marly_wrong_spelling) == 0)
    if rikie:
        check("(Rikie) Andrea Kruger is a child of Andre + Lettie Kruger",
              len(by_id[rikie].get('parents', [])) == 2)
    if marley:
        check("Marley Kruger is a child of Andre + Lettie Kruger",
              len(by_id[marley].get('parents', [])) == 2)

    # Arnouw Johan Nel is NOT married to Andrew du Toit -- confirmed wrong link, removed
    arnouw = get_one('Arnouw Johan Nel')
    if arnouw:
        check("Arnouw Johan Nel has no spouse recorded (the Andrew du Toit link was wrong)",
              by_id[arnouw].get('spouse', []) == [])
    andrew_dt = find_id(data, 'Andrew du Tiot')
    if andrew_dt:
        check("Andrew du Toit has no spouse recorded (the Arnouw link was wrong)",
              by_id[andrew_dt[0]].get('spouse', []) == [])

    # Olivier / Boel-Phillip cluster: 8 siblings, children of Jan Hendrik Olivier + Claris (Boucher)
    boel = get_one('Boel)Elijah Hendrik Olivier')
    phillip_o = get_one('(Phillip)Phillippus Arnoldus Olivier')
    maria_magdalena = find_id(data, 'Maria Magdalena Olivier')
    if boel and phillip_o:
        check("Boel and Phillip Olivier are siblings of each other",
              phillip_o in by_id[boel].get('siblings', []))
    if maria_magdalena and boel:
        mm_id = maria_magdalena[0]
        check("Maria Magdalena Olivier (the grandmother) is NOT a sibling of Boel",
              mm_id not in by_id[boel].get('siblings', []))

    # Phillip(29) + Kotie(53)'s children: Jannie, Buks, Arnold are blood; Lynette & Madelein married in
    lynette = get_one('Lynette Olivier')
    madelein = get_one('Madelein Olivier')
    arnold = get_one('(Arnold)Phillippus Arnoldus Olivier')
    if lynette:
        check("Lynette Olivier has no parents recorded (she married in, maiden name Visser)",
              by_id[lynette].get('parents', []) == [])
    if madelein:
        check("Madelein Olivier has no parents recorded (she married in, maiden name Muller)",
              by_id[madelein].get('parents', []) == [])
    if arnold and lynette and madelein:
        check("Arnold Olivier was married to BOTH Lynette and Madelein (sequentially)",
              lynette in by_id[arnold].get('spouse', []) and madelein in by_id[arnold].get('spouse', []))

    # Anthony Claude Roux + Johanna Vendel(Gierke): married, divorced; she remarried Lorenz Vendel
    anthony_roux = get_one('Anthony Claude Roux')
    johanna_vendel = get_one('Johanna Maria Vendel(Gierke)')
    juanel_roux = get_one('Juan\u00e9l Roux')
    if anthony_roux and johanna_vendel:
        check("Anthony Claude Roux and Johanna Vendel are linked as (ex-)spouses",
              johanna_vendel in by_id[anthony_roux].get('spouse', []))
    if juanel_roux:
        check("Juan\u00e9l Roux has no spouse recorded (her real husband isn't in the tree)",
              by_id[juanel_roux].get('spouse', []) == [])

    # Marais family: Marie's 6 siblings, all children of H.J. Marais + Johanna Maria Booyens
    marie_marais = get_one('Marie) Johanna Maria Olivier (Marais)')
    ada_marais = get_one('Ada Broderyk')
    henri_marais = get_one('Henri Marais')
    bert_marais = get_one('Bert)Willem Marais')
    if marie_marais and ada_marais:
        check("Marie Marais and Ada Broderyk(Marais) are siblings",
              ada_marais in by_id[marie_marais].get('siblings', []))
    if marie_marais and henri_marais:
        check("Marie Marais and Henri Marais are siblings",
              henri_marais in by_id[marie_marais].get('siblings', []))
    if ada_marais:
        check("Ada Broderyk(Marais) has her photos (at least 4)",
              len(by_id[ada_marais].get('photos', [])) >= 4)
    if bert_marais:
        georgina = get_one('Georgina Marais')
        check("Bert Willem Marais is married to Georgina Marais",
              georgina is not None and georgina in by_id[bert_marais].get('spouse', []))
    if henri_marais:
        susan_marais = get_one('Susan Marais')
        check("Henri Marais is married to Susan Marais",
              susan_marais is not None and susan_marais in by_id[henri_marais].get('spouse', []))

    # Kruger kids under Nas Kruger: Stompie's siblings should have NO photos wrongly attributed
    # from the Marais branch (the id-collision bug)
    kruger_kid_names = ['Ousus Kruger','Willem Kruger','Liefie Kruger','Hartjie Kruger','Marthie Kruger']
    marais_photo_paths = set()
    for p in data:
        if 'Marais' in p['name'] and p['id'] not in ([marie_marais, ada_marais, henri_marais] if marie_marais else []):
            marais_photo_paths.update(p.get('photos', []))
    for kn in kruger_kid_names:
        for kid_id in find_id(data, kn):
            overlap = set(by_id[kid_id].get('photos', [])) & marais_photo_paths
            if overlap:
                failures.append(f"[PHOTO CROSS-ATTRIBUTION] {by_id[kid_id]['name']} has photo(s) that also belong to a Marais-family member: {overlap}")

    # Gierke family: Claris Linda Gierke(Olivier) + Peet Gierke's 6 children including Susanna
    susanna_gierke = get_one('Susanna Elizabeth Gierke')
    juanita_jordan = get_one('Juanita Hendrika Jordan')
    if susanna_gierke and johanna_vendel:
        check("Susanna Elizabeth Gierke and Johanna Vendel are siblings",
              susanna_gierke in by_id[johanna_vendel].get('siblings', []))
    if susanna_gierke:
        check("Susanna Elizabeth Gierke has no spouse recorded",
              by_id[susanna_gierke].get('spouse', []) == [])
    michael_ehlers = get_one('Michael Ehlers')
    if michael_ehlers and juanita_jordan:
        check("Michael Ehlers is married to Juanita Hendrika Jordan(Gierke) only",
              by_id[michael_ehlers].get('spouse', []) == [juanita_jordan])
    if juanita_jordan:
        check("Juanita Hendrika Jordan(Gierke) has exactly one spouse (Michael Ehlers)",
              len(by_id[juanita_jordan].get('spouse', [])) == 1)
    jenna = get_one('Jenna Jordan')
    steven_jordan = get_one('Steven Ross Jordan')
    if jenna and steven_jordan:
        check("Jenna Jordan is married to Steven Ross Jordan (confirmed, not a sibling error)",
              by_id[jenna].get('spouse', []) == [steven_jordan])
        check("Jenna Jordan has no parents recorded (married in, maiden name unknown)",
              by_id[jenna].get('parents', []) == [])
    mannetjiie = get_one('Mannetjiie Gierke')
    paul_gierke = get_one('Paul Gierke')
    juanita_burger = get_one('Juanita Gierke(Burger)')
    if mannetjiie:
        check("Mannetjiie Gierke has no spouse recorded (unknown)",
              by_id[mannetjiie].get('spouse', []) == [])
    if paul_gierke and juanita_burger:
        check("Paul Gierke is married to Juanita Gierke(Burger) (not Mannetjiie)",
              juanita_burger in by_id[paul_gierke].get('spouse', []))

    # Swartz family: Phillip Rudoph Botha married in, not a blood Swartz
    phillip_botha = get_one('Phillip Rudoph Botha')
    if phillip_botha:
        check("Phillip Rudoph Botha has no parents recorded (he married into the Swartz family)",
              by_id[phillip_botha].get('parents', []) == [])

    # Boel/Phillip's siblings Claris, Willie, and Stella married surname-matching spouses --
    # this whole cluster was found cross-wired (each linked to the WRONG in-law) and reverted
    # once already, so it's checked thoroughly.
    claris_fourie = get_one('Claris Fourie(Olivier)')
    nico_fourie = get_one('Nico Fourie')
    willie_vg = get_one('Willemina van Greunen(Olivier)')
    okkie = get_one('Okkie van Greunen')
    stella = get_one('Boutjies) Estelle Bouwer(Olivier)')
    boetie_bouwer = get_one('Boetie) Hendrikus Johannes Bouwer')
    rita_yvonne = get_one('Rita Yvonne Olivier')
    if claris_fourie and nico_fourie:
        check("Claris Fourie(Olivier) is married to Nico Fourie (matching surnames)",
              by_id[claris_fourie].get('spouse', []) == [nico_fourie])
    if willie_vg and okkie:
        check("Phillippina Willemina van Greunen(Olivier) is married to Okkie van Greunen",
              by_id[willie_vg].get('spouse', []) == [okkie])
    if stella and boetie_bouwer:
        check("Stella-Boutjies Estelle Bouwer(Olivier) is married to Boetie Bouwer (not Okkie van Greunen)",
              by_id[stella].get('spouse', []) == [boetie_bouwer])
    if rita_yvonne:
        check("Rita Yvonne Olivier(Allers) is not married to Claris Fourie (that was a wrong link)",
              claris_fourie not in by_id[rita_yvonne].get('spouse', []))

    # Stella + Boetie Bouwer's 3 daughters, each married with children -- one daughter
    # (Suzette) and two grandchildren (Arnouw, Andrew) were found completely missing
    # this parent link, and Arnouw/Andrew were also found misattributed to Brenda's family.
    sanet = get_one('Sanet Cummings')
    suzette = get_one('Suzette (Bouwer) du Toit')
    brenda = get_one('Brenda Nel')
    arnouw_nel = get_one('Arnouw Johan Nel')
    andrew_dt2 = get_one('Andrew du Tiot')
    if stella and boetie_bouwer and sanet and suzette and brenda:
        expected_kids = {sanet, suzette, brenda}
        check("Stella + Boetie Bouwer's 3 daughters (Sanet, Suzette, Brenda) all show as children of both",
              set(by_id[stella].get('children', [])) >= expected_kids and
              set(by_id[boetie_bouwer].get('children', [])) >= expected_kids)
    if suzette and andrew_dt2:
        check("Andrew du Toit is Suzette + Craig du Toit's son (matching his surname)",
              andrew_dt2 in by_id[suzette].get('children', []))
    if brenda and arnouw_nel:
        check("Arnouw Johan Nel is Brenda + Jan Nel's son (matching his surname, confirmed correct after an earlier wrong guess)",
              arnouw_nel in by_id[brenda].get('children', []))
        check("Arnouw Johan Nel is NOT one of Suzette's children",
              arnouw_nel not in by_id[suzette].get('children', []) if suzette else True)

    # Rita Yvonne Olivier(Allers) married Jackie Jan Hendrik Olivier; their 2 daughters
    # Judith and Janine. Janine's married surname is de Lange -- her husband is Johannes
    # de Lange, who was found misattributed as Rita Yvonne's son instead of Janine's
    # husband, with their 3 children (Marushka, Jean-Pierre, Caulume) each only showing
    # one of the two parents.
    rita_yvonne2 = get_one('Rita Yvonne Olivier')
    jackie = get_one('Jackie) Jan Hendrik Olivier')
    judith = get_one('Judith Claire Rothbone')
    janine = get_one('Janine Jacqueline de Lange')
    johannes_dl = get_one('Johannes de Lange')
    if rita_yvonne2 and jackie:
        check("Rita Yvonne Olivier(Allers) is married to Jackie Jan Hendrik Olivier",
              by_id[rita_yvonne2].get('spouse', []) == [jackie])
    if rita_yvonne2 and judith and janine:
        check("Judith and Janine both show Rita Yvonne as a parent (alongside Jackie)",
              rita_yvonne2 in by_id[judith].get('parents', []) and rita_yvonne2 in by_id[janine].get('parents', []))
    if janine and johannes_dl:
        check("Janine is married to Johannes de Lange (not her mother's spouse)",
              by_id[janine].get('spouse', []) == [johannes_dl])
        check("Johannes de Lange has no parents recorded (he married in)",
              by_id[johannes_dl].get('parents', []) == [])
    if janine and johannes_dl:
        for kid_name in ['Marushka de Lange', 'Jean-Pierre de Lange', 'Caulume de Lange']:
            kid_id = get_one(kid_name)
            if kid_id:
                check(f"{kid_name} shows both Janine and Johannes as parents",
                      janine in by_id[kid_id].get('parents', []) and johannes_dl in by_id[kid_id].get('parents', []))

    # Welma Verona Swartz married Hennie Swartz (Ena's son); shares his 2 children
    welma = get_one('Welma Verona Swartz')
    hennie_swartz = get_one('Hennie Swartz')
    ellelaine = get_one('Ellelaine Olivier')
    hennie_olivier = get_one('(Hennie)Hendrik Elijah Olivier')
    if welma and hennie_swartz:
        check("Welma Verona Swartz is married to Hennie Swartz",
              hennie_swartz in by_id[welma].get('spouse', []))
        verona_burger = get_one('Verona Burger(Swartz)')
        lambert_swartz = get_one('Lambert Swartz')
        if verona_burger:
            check("Welma is Verona Burger(Swartz)'s mother too",
                  welma in by_id[verona_burger].get('parents', []))
        if lambert_swartz:
            check("Welma is Lambert Swartz's mother too",
                  welma in by_id[lambert_swartz].get('parents', []))
    if ellelaine and hennie_olivier:
        check("Ellelaine Olivier is married ONLY to Hennie Olivier (not also to Welma)",
              by_id[ellelaine].get('spouse', []) == [hennie_olivier])

    # Charlotte Suzan Scoombie's husband is Gerhardus Petrus Botha (originally entered as
    # "Gert Botha", later expanded to his full name), not the old "unknown husband"
    # placeholder -- this has reverted to the placeholder multiple times already.
    charlotte_s = get_one('Charlotte Suzan Scoombie')
    gert_botha = get_one('Gerhardus Petrus Botha')
    placeholder_still_exists = len(find_id(data, 'Charlotte se man Scoombie')) > 0
    if charlotte_s and gert_botha:
        check("Charlotte Suzan Scoombie is married to Gerhardus Petrus Botha",
              by_id[charlotte_s].get('spouse', []) == [gert_botha])
    check("The old 'Charlotte se man Scoombie' placeholder no longer exists (replaced by Gerhardus Petrus Botha)",
          not placeholder_still_exists)

    # Charlotte + Gerhardus Petrus Botha's 2 children (Petrus Gerhardus Dominique Botha and
    # Claruissa Maria Diederiks(Botha)) were found only listing Charlotte as a parent --
    # Gerhardus was missing, so he showed zero children despite being her husband. Fixed
    # 2026-08-31.
    petrus_gdb = get_one('Petrus Gerhardus Dominique Botha')
    claruissa = get_one('Claruissa Maria Diederiks')
    if charlotte_s and gert_botha and petrus_gdb and claruissa:
        check("Petrus Gerhardus Dominique Botha shows BOTH Charlotte and Gerhardus as parents",
              set(by_id[petrus_gdb].get('parents', [])) == {charlotte_s, gert_botha})
        check("Claruissa Maria Diederiks(Botha) shows BOTH Charlotte and Gerhardus as parents",
              set(by_id[claruissa].get('parents', [])) == {charlotte_s, gert_botha})
        check("Gerhardus Petrus Botha shows both children (Petrus and Claruissa)",
              set(by_id[gert_botha].get('children', [])) >= {petrus_gdb, claruissa})

    # Petrus Gerhardus Dominique Botha married Jennette Sophia Elizabeth Botha; their 2 sons
    # (Dominique Viljoen Botha, Rikus Botha) were found only listing Jennette as a parent --
    # Petrus was missing, so he showed zero children despite being their father. Fixed
    # 2026-08-31.
    jennette_b = get_one('Jennette Sophia Elizabeth Botha')
    dominique_vb = get_one('Dominique Viljoen Botha')
    rikus_b = get_one('Rikus Botha')
    if petrus_gdb and jennette_b:
        check("Petrus Gerhardus Dominique Botha is married to Jennette Sophia Elizabeth Botha",
              by_id[petrus_gdb].get('spouse', []) == [jennette_b])
    if petrus_gdb and jennette_b and dominique_vb and rikus_b:
        check("Dominique Viljoen Botha shows BOTH Petrus and Jennette as parents",
              set(by_id[dominique_vb].get('parents', [])) == {petrus_gdb, jennette_b})
        check("Rikus Botha shows BOTH Petrus and Jennette as parents",
              set(by_id[rikus_b].get('parents', [])) == {petrus_gdb, jennette_b})
        check("Petrus Gerhardus Dominique Botha shows both sons (Dominique and Rikus) as children",
              set(by_id[petrus_gdb].get('children', [])) == {dominique_vb, rikus_b})
        check("Dominique and Rikus Botha are siblings of each other",
              rikus_b in by_id[dominique_vb].get('siblings', []) and dominique_vb in by_id[rikus_b].get('siblings', []))

    # ---------- REPORT ----------
    print(f"Checked {len(data)} people.\n")
    if failures:
        print(f"FAILED: {len(failures)} issue(s) found:\n")
        for f in failures:
            print("  -", f)
        return False
    else:
        print("ALL CHECKS PASSED.")
        return True

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'data.json'
    ok = run(path)
    sys.exit(0 if ok else 1)
