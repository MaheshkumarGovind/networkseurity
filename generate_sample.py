import pandas as pd
import numpy as np
import os

# Create sample phishingData.csv with network security features
np.random.seed(42)  # For reproducibility
n_samples = 1000

data = {
    'src_ip': [f"192.168.1.{i}" for i in range(n_samples)],
    'dst_ip': np.random.choice(['10.0.0.1', '10.0.0.2', '172.16.0.1'], n_samples),
    'protocol': np.random.choice(['TCP', 'UDP', 'ICMP'], n_samples),
    'label': np.random.choice(['normal', 'phishing', 'attack'], n_samples, p=[0.7, 0.2, 0.1]),
    'bytes': np.random.randint(100, 10000, n_samples),
    'packets': np.random.randint(1, 100, n_samples),
    'url_length': np.random.randint(10, 100, n_samples),  # Phishing-specific feature
    'has_ip': np.random.choice([0, 1], n_samples)  # e.g., IP in URL (phishing indicator)
}

df = pd.DataFrame(data)
os.makedirs('Network_Data', exist_ok=True)
df.to_csv('Network_Data/phishingData.csv', index=False)
print(f"✅ Sample CSV created: Network_Data/phishingData.csv ({n_samples} rows, {len(data)} columns)")
print("\nSample rows:")
print(df.head())