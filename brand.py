"""Reversible presentation copy; existing stored content and records stay intact."""

NAME = 'The Godfather'

DEFAULT_DISPLAY_COPY = {
    'origin': 'Τα παιδιά πίσω από τη Philoxenia by Hustle Hours ήταν μέρος της παρέας μας. Ανοίγοντας τον χώρο και τον κόσμο τους σε νέους builders, άναψαν τη σπίθα. Το The Godfather είναι η δική μας ανεξάρτητη προσπάθεια να μεταφέρουμε αυτή τη νοοτροπία παντού.',
    'hero_intro': 'Θέλουμε να χτίσουμε ένα παγκόσμιο δίκτυο builders που δημιουργούν, ανεβαίνουν και τραβούν ο ένας τον άλλο πιο ψηλά. Στο δίκτυο The Godfather βρίσκεις φιλοξενία, εμπειρία και ανθρώπους που σε βοηθούν να κάνεις το επόμενο βήμα.',
    'manifesto': 'Κι εμείς βρήκαμε κάποτε τους δικούς μας ανθρώπους: έναν Godfather και μια παρέα που μας έκανε χώρο, μοιράστηκε όσα ήξερε και πίστεψε σε εμάς πριν έχουμε πολλά να δείξουμε. Αυτή η εμπειρία άλλαξε το τι θεωρούσαμε εφικτό για τη ζωή μας.',
}


def display_content(stored, defaults):
    """Keep custom copy; replace old brand references only in the rendered view."""
    result = dict(stored)
    for key, value in result.items():
        if key in DEFAULT_DISPLAY_COPY and value == defaults.get(key):
            value = DEFAULT_DISPLAY_COPY[key]
        result[key] = value.replace('της Greek Mafia', 'του δικτύου The Godfather').replace('Η Greek Mafia', 'Το δίκτυο The Godfather').replace('Greek Mafia', NAME)
    return result
