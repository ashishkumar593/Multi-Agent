# Production Cloud Deployment Guide (Docker & AWS EC2)

This guide documents the procedures for deploying the **AI Research & Report Agent** onto an AWS EC2 Ubuntu instance using Docker Compose, Nginx, and automated TLS/SSL.

---

## 1. AWS EC2 Provisioning

### Recommended Server Specs
- **Instance Type**: `t3.large` or `c6i.large` (2 vCPUs, 4–8 GB RAM)
- **Root Volume**: 50 GB gp3 SSD
- **Base OS**: Ubuntu 22.04 LTS

### Security Group Inbound Rules
| Type | Port | Protocol | Source | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **SSH** | 22 | TCP | Your Admin IP | Secure Remote Admin |
| **HTTP** | 80 | TCP | 0.0.0.0/0 | Web Traffic & ACME Challenge |
| **HTTPS** | 443 | TCP | 0.0.0.0/0 | Encrypted Public Traffic |

*Note: PostgreSQL (5432) and Redis (6379) are kept strictly within internal Docker networks and are never exposed publicly.*

---

## 2. Server Bootstrap Script

Run the automated host setup script:
```bash
curl -fsSL https://raw.githubusercontent.com/your-org/ai-research-agent/main/infrastructure/aws/user-data.sh | sudo bash
```

---

## 3. Application Deployment via Docker Compose

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/ai-research-agent.git /opt/ai-research-agent
   cd /opt/ai-research-agent
   ```
2. **Configure Environment Secrets**:
   ```bash
   cp .env.example .env
   nano .env
   # Add OPENAI_API_KEY, TAVILY_API_KEY, and strong DB credentials
   ```
3. **Launch Multi-Container Services**:
   ```bash
   docker compose up --build -d
   ```
4. **Verify Container Health**:
   ```bash
   docker compose ps
   ```

---

## 4. HTTPS / TLS Automation via Certbot

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```
Certbot automatically provisions Let's Encrypt certificates and schedules auto-renewal via systemd timers.
