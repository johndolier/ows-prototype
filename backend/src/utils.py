# HELPER FUNCTIONS


def normalize_scoring_range(results, min_score, max_score):
    range = max_score - min_score
    for result in results:
        if range == 0:
            # set everything to 0.5
            result['score'] = 0.5
        else:
            result['score'] = (result['score'] - min_score) / range
    return results