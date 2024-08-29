import pandas as pd
from collections import Counter
import itertools
import re

def group_keyword(df, stop_words, min_group_size=2, ngram_size=2, keyword_column='Parent Keyword'):
    df[keyword_column] = df[keyword_column].astype(str)
    all_words = list(itertools.chain(*df[keyword_column].str.lower().str.split()))
    word_freq = Counter(all_words)
    common_terms = {word for word, freq in word_freq.items() if freq > 1 and word not in stop_words and len(word) > 2}

    grouped_dfs = []
    for keyword in df[keyword_column]:
        words = re.findall(r'\b\w+\b', keyword.lower())
        if len(words) >= ngram_size:
            ngrams = [tuple(words[i:i + ngram_size]) for i in range(len(words) - ngram_size + 1)]
            groups = set()
            for ngram in ngrams:
                if all(term in common_terms or term.isdigit() for term in ngram):
                    groups.add(" ".join(ngram))
            if groups:
                grouped_dfs.extend([pd.DataFrame({'Group': [group], 'Keyword': [keyword]}) for group in groups])

    grouped_keyword_df = pd.concat(grouped_dfs, ignore_index=True)
    filtered_groups = grouped_keyword_df.groupby('Group').filter(lambda x: len(x) >= min_group_size)
    return filtered_groups

def calculate_group_metrics(df, grouped_df, keyword_column='Parent Keyword', clicks_column='Volume', difficulty_column='Difficulty', traffic_potential_column='Traffic potential'):
    metrics = {}
    for group in grouped_df['Group'].unique():
        keyword_in_group = grouped_df[grouped_df['Group'] == group]['Keyword'].tolist()
        total_volume = df[df[keyword_column].isin(keyword_in_group)][clicks_column].sum()
        avg_kd = df[df[keyword_column].isin(keyword_in_group)][difficulty_column].mean()
        traffic_potential = df[df[keyword_column].isin(keyword_in_group)][traffic_potential_column].sum()
        avg_traffic_potential = traffic_potential / len(keyword_in_group) if len(keyword_in_group) > 0 else 0
        metrics[group] = {
            'Total Volume': total_volume,
            'Avg. KD': avg_kd,
            'Traffic Potential': traffic_potential,
        }
    return metrics

def calculate_opportunity_score(df, volume_column='Volume', difficulty_column='Difficulty', cpc_column='CPC'):
    df['Opportunity Score'] = df.apply(
        lambda row: row[volume_column] * (1 - (row[difficulty_column] / 100)) * (row[cpc_column] / 100) if row[cpc_column] else 0, axis=1
    )
    return df

def read_csv_file(uploaded_file):
    encodings = ['utf-8', 'latin1', 'utf-16']
    for encoding in encodings:
        try:
            return pd.read_csv(uploaded_file, encoding=encoding)
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    st.error("Error parsing the file. Please check the encoding and the file format.")
    return None
