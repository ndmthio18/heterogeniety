"""Reproduce Table 2 arithmetic without changing source values or model inputs."""
import csv
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2011WR010776'
ROWS = [
    ('Homo-Fine', 'H', '3.47e-5', '9.79e-4', '1.16e-6'),
    ('Homo-Fine', 'L', '1.74e-5', '1.65e-3', '1.74e-6'),
    ('Hetero Fine 1', 'H', '4.63e-5', '4.89e-4', '2.16e-6'),
    ('Hetero Fine 1', 'L', '3.47e-5', '1.16e-3', '2.55e-6'),
    ('Hetero Fine 2', 'H', '5.79e-5', '9.17e-4', '2.31e-6'),
    ('Hetero Fine 2', 'L', '4.63e-5', '1.71e-3', '6.17e-6'),
]

def half_last_digit(value):
    return D(5) * D(10) ** (D(value).as_tuple().exponent - 1)

def main():
    records = []
    for case, pe, j_text, l_text, ds_text in ROWS:
        j, length, published = map(D, (j_text, l_text, ds_text))
        dc, air = D('.015'), D('2.6695e-5')
        calculated = j * length / dc
        dj, dl, dd = map(half_last_digit, (j_text, l_text, '.015'))
        low = (j-dj)*(length-dl)/(dc+dd)
        high = (j+dj)*(length+dl)/(dc-dd)
        dp = half_last_digit(ds_text)
        overlap = low <= published+dp and high >= published-dp
        records.append(dict(
            case=case, PE=pe, J_reported=j_text,
            J_original_header='Kg s^-1 m^2', J_dimensional_unit='kg m^-2 s^-1',
            L_salt_m=l_text, Delta_C_s_kg_m3='.015', D_s_published_m2_s=ds_text,
            D_s_recomputed_m2_s=str(calculated),
            recomputed_minus_published_percent=str((calculated/published-1)*100),
            D_air_reference_m2_s=str(air), D_air_reference_T_C='25',
            published_Ds_over_Dair=str(published/air),
            recomputed_Ds_over_Dair=str(calculated/air),
            recomputed_rounding_low_m2_s=str(low), recomputed_rounding_high_m2_s=str(high),
            rounding_intervals_overlap=str(overlap),
            PE_cm_day='3.84' if pe == 'H' else '2.4',
            RH_assumed_fraction='.5', atmospheric_T_setpoint='not verified',
            initial_NaCl_wt_percent='25', supply='constant head', stage='SS3',
            transcription_status='publisher table and original paper parsed text agree',
            arithmetic_status='does not reproduce published coefficient',
            source=SOURCE, source_location='Table 2; Eq 9; paragraphs 25-28,35-36'))
    assert len(records) == 6
    assert not any(r['rounding_intervals_overlap'] == 'True' for r in records)
    path = ROOT / 'results' / 'NACHSHON_2011_TABLE2_VERIFIED.csv'
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    for row in records:
        print(row['case'], row['PE'], row['D_s_recomputed_m2_s'],
              row['recomputed_minus_published_percent'], row['published_Ds_over_Dair'])

if __name__ == '__main__':
    main()
