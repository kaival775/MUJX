# Moving to Production (Blockchain)

You asked: **"Can I do everything for free in Prod?"**
**YES!** The answer is **Public Testnets**.

## 🚀 The "Free Production" Solution: Public Testnets

A **Testnet** (like Sepolia or Polygon Amoy) is a real, public blockchain that lives on the internet. It works exactly like the main blockchain updates 24/7, accessible from anywhere—but the "money" (ETH/MATIC) is **FREE**.

This is perfect for your specific needs because:
1.  **Zero Cost**: You get free crypto from "Faucets" (websites that give mock crypto).
2.  **Publicly Accessible**: Anyone with internet can interact with your contract.
3.  **Permanent-ish**: Your data stays there (unlike local Ganache which resets when you close it).

---

## Steps to Go Live for FREE (Sepolia Testnet)

### 1. Get a Wallet & "Free Money"
1.  Open **MetaMask** and switch network to **"Sepolia Test Network"** (enable "Show test networks" in settings).
2.  Copy your wallet address.
3.  Go to a **Sepolia Faucet** (e.g., [Google Cloud Faucet](https://cloud.google.com/application/web3/faucet/ethereum/sepolia) or [Alchemy Faucet](https://www.alchemy.com/faucets/ethereum-sepolia)).
4.  Paste address -> Click "Send Me ETH". You now have fake ETH to pay for gas!

### 2. Get a Free RPC URL
1.  Sign up for a free account at [Alchemy](https://www.alchemy.com).
2.  Create a new App -> Choose Chain: **Ethereum**, Network: **Sepolia**.
3.  Copy the **HTTPS URL** (this is your Gateway).

### 3. Updates Keys
Update your `backend/.env`:
```ini
# FREE PUBLIC TESTNET (Sepolia)
BLOCKCHAIN_RPC_URL="https://eth-sepolia.g.alchemy.com/v2/YOUR_ALCHEMY_KEY..."
PRIVATE_KEY="<Your Metamask Private Key>"
```

### 4. Deploy
Run: `python deploy.py`
This deploys your contract to the **Real Public Internet** (Sepolia), but costs you $0.

---

## Alternative: Real Mainnet (Not Free)

## Steps to Go Live

### 1. Choose a Network
-   **Polygon (Recommended)**: Very low fees (< $0.05 per TX), fast, and eco-friendly.
-   **Ethereum**: High fees ($5 - $50+ per TX), highly secure.
-   **Sepolia Testnet**: Free, public test network (good for staging).

### 2. Get an RPC Provider
You cannot connect to the global blockchain directly from a simple script without a node. You need an RPC provider (Gateway).
-   **Alchemy** (https://www.alchemy.com) - Free tier available.
-   **Infura** (https://www.infura.io)

### 3. Setup a Wallet & Private Key
-   Create a Metamask wallet.
-   Export the **Private Key** (Keep this secure! Never commit it to GitHub).
-   Fund the wallet with real crypto (ETH or MATIC) to pay for "Gas" (transaction fees).

### 4. Update Configuration
In your `backend/.env` file, you will update the variables:

```ini
# DEVELOPMENT (Current)
BLOCKCHAIN_RPC_URL="https://127.0.0.1:8545"
PRIVATE_KEY="<Private key from Ganache>"

# PRODUCTION (Future)
# BLOCKCHAIN_RPC_URL="https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY"
# PRIVATE_KEY="<Your Real Wallet Private Key>"
```

### 5. Deploy to Production
Run your deployment script with the new config.
```bash
python deploy.py
```
This will deploy your `LandRegistry` contract to the real network and save the new address.

### 6. Update Application
Restart your backend. It will now talk to the live blockchain!
