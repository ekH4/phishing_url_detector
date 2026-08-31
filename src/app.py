import streamlit as st
import pandas as pd
import joblib

model = joblib.load("models/logreg_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_cols = joblib.load("models/feature_columns.pkl")
tld_freq_map = joblib.load("models/tld_freq_map.pkl")

st.title("🔗 Phishing URL Risk Checker (Prototype)")
st.warning("⚠️ This is a prototype for educational purposes, not a production security tool.")

url_input = st.text_input("Enter a URL to check:")

from urllib.parse import urlparse

def extract_features(url, tld_freq_map):
    parsed = urlparse(url)
    domain = parsed.netloc
    tld = domain.split('.')[-1] if '.' in domain else ''

    features = {
        'URLLength': len(url),
        'DomainLength': len(domain),
        'IsDomainIP': 1 if domain.replace('.', '').isdigit() else 0,
        'TLDLength': len(tld),
        'NoOfSubDomain': domain.count('.') - 1 if domain.count('.') > 1 else 0,
        'HasObfuscation': 1 if '%' in url else 0,
        'NoOfObfuscatedChar': url.count('%'),
        'ObfuscationRatio': url.count('%') / len(url) if len(url) > 0 else 0,
        'NoOfLettersInURL': sum(c.isalpha() for c in url),
        'LetterRatioInURL': sum(c.isalpha() for c in url) / len(url) if len(url) > 0 else 0,
        'NoOfDegitsInURL': sum(c.isdigit() for c in url),
        'DegitRatioInURL': sum(c.isdigit() for c in url) / len(url) if len(url) > 0 else 0,
        'NoOfEqualsInURL': url.count('='),
        'NoOfQMarkInURL': url.count('?'),
        'NoOfAmpersandInURL': url.count('&'),
        'NoOfOtherSpecialCharsInURL': sum(not c.isalnum() for c in url),
        'SpacialCharRatioInURL': sum(not c.isalnum() for c in url) / len(url) if len(url) > 0 else 0,
        'TLDLegitimateProb': tld_freq_map.get(tld, 0),
        'TLD_freq': tld_freq_map.get(tld, 0),
    }
    return features

if url_input:
    feats = extract_features(url_input, tld_freq_map)

    # temporarily zero out IsDomainIP influence to test
    # feats_test = feats.copy()
    # feats_test['IsDomainIP'] = 0
    # feats_df_test = pd.DataFrame([feats_test])[feature_cols]
    # feats_scaled_test = scaler.transform(feats_df_test)
    # print(model.predict_proba(feats_scaled_test))

    # st.write("Raw extracted features:", feats)
    # st.write("Feature columns expected by model:", feature_cols)
    # feats_df = pd.DataFrame([feats])[feature_cols]
    # st.write("Feats DataFrame (ordered):", feats_df)
    # feats_scaled = scaler.transform(feats_df)
    # st.write("Scaled features:", feats_scaled)

    feats_df = pd.DataFrame([feats])[feature_cols]  # ensure correct column order
    feats_scaled = scaler.transform(feats_df)

    pred = model.predict(feats_scaled)[0]
    proba = model.predict_proba(feats_scaled)[0][1]

    if pred == 1:
        st.error(f"⚠️ Likely PHISHING (confidence: {proba:.1%})")
    else:
        st.success(f"✅ Likely SAFE (confidence: {(1-proba):.1%})")

    
    st.write("Extracted features:", feats_df)