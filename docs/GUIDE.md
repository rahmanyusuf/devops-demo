# DevOps L5 – AWS Learner Lab build and recording guide

## 0. Read this first (blunt version)

- **I could not read your PowerPoint.** The file is encrypted or protected (it is not a normal .pptx), so
  everything below is built from the assessment brief only. If your tutor's deck prescribes a specific
  architecture or tool, re-export it (PDF, or "Save a copy" without the sensitivity label) and check this design
  against it before building.
- **Nobody can guarantee 80-100%.** The app is not marked. Marks come from (a) a working pipeline with several
  advanced features, (b) *justified* design decisions with *accurate* citations, (c) critical reflection with
  advantages **and** disadvantages. Most people lose marks by describing what they clicked instead of
  evaluating it.
- **This has been linted and unit-tested locally, but never deployed to a real AWS account.** Expect one or two
  Learner Lab-specific failures. Dry-run the full pipeline at least twice before you record anything.
- The brief says the AWS-only option "doesn't utilise source control or fully utilise the pipeline". This design
  deliberately uses GitHub + Actions + AWS so you have source control, CI, CD and IaC, which is what the top
  band descriptors ("extensive advanced features", "robust environment") are really asking for.

## 1. What you are building

```
Developer -> GitHub (main)
                |  push / PR
                v
        GitHub Actions
   [CI gate] flake8 | pytest + 80% coverage | pip-audit | cfn-lint | Checkov
                |  (pass)
                v
   [Manual approval]  GitHub Environment "production"
                v
   [Build] zip app, tag with commit SHA -> S3 (immutable artefact)
                v
   [Deploy] CloudFormation (IaC) ---> VPC, 2 public subnets, ALB, Target Group,
                                      Launch Template, Auto Scaling Group (2 x t3.micro),
                                      CloudWatch alarms, scaling policy
                v   rolling update (1 at a time, health-signalled)
   [Verify] smoke test: /health version == commit SHA ; drift detection
                v
   Failure at any point -> CloudFormation automatic rollback
```

Why this design (use these as your "rationale" points):

| Decision | Reason | Trade-off to mention |
|---|---|---|
| CloudFormation as IaC | Native to AWS, no state file to manage, works with Learner Lab's fixed `LabRole` | AWS-only lock-in; verbose versus Terraform/CDK |
| Immutable artefacts named by SHA | Traceability, repeatable deploys, easy rollback | Storage grows; needs lifecycle rules |
| ASG + ALB, rolling update | Zero-downtime, self-healing, shows load balancing live | Costs more than one instance; blue/green would be safer but heavier |
| `cfn-signal` health gating | Bad releases fail and roll back automatically | Slower deploys (minutes) |
| GitHub Environments approval | Separation of duties / change control | Manual step slows lead time |
| Checkov and pip-audit | "Shift-left" security (DevSecOps) | Noisy; lab has no HTTPS or logging by design |
| Static AWS keys in GitHub secrets | Only option in Learner Lab (cannot create IAM OIDC provider/roles) | **Weakness**: long-lived-credential risk; real systems should use OIDC. Say this out loud, it is good reflection material |
| Public subnets, no NAT | Avoids NAT cost in the lab | Production would use private subnets plus NAT/endpoints |
| In-memory app state | Keeps the app trivial | Not durable across instances; production would use DynamoDB/RDS |

## 2. Rubric mapping – where the marks are

| Criterion (weight) | What 80%+ looks like | What to show / say |
|---|---|---|
| Functionality (40%) | App runs; pipeline has *extensive* advanced features; IaC creates a *robust* environment | Quality gate, security scans, approval gate, immutable artefacts, rolling update, auto-rollback, smoke test, drift detection, autoscaling, alarms, teardown workflow |
| DevOps concepts (20%) | Deep, nuanced, linked to theory | CALMS, the Three Ways, CI vs continuous delivery vs deployment, IaC benefits (idempotence, repeatability), shift-left, DORA metrics, with citations |
| Design/architecture (20%) | Every component and its interactions justified | Walk the diagram; justify each row of the table above; mention Well-Architected pillars |
| Reflection (20%) | Insightful, evidence-based, tied to industry | Your measured pipeline numbers, what broke, what you would change, the credential weakness, relevance to your own organisation (e.g. change-management evidence and segregation of duties in regulated or audit environments) |

## 3. Setup steps (Learner Lab)

1. Start the lab (AWS Academy > Learner Lab > **Start Lab**), wait for the green dot, open the console.
   Stay in **us-east-1** (Learner Lab only allows us-east-1 and us-west-2; the workflows assume us-east-1).
2. In the lab panel click **AWS Details > AWS CLI: Show** and copy the three values (access key, secret key,
   session token).
3. In CloudShell or your terminal check the instance profile exists:
   `aws iam list-instance-profiles --query "InstanceProfiles[].InstanceProfileName"`
   It should list `LabInstanceProfile`. If the name differs, change the `InstanceProfileName` default in
   `infra/template.yaml`.
4. Create a GitHub repo and push this folder to `main`.
5. Repo **Settings > Secrets and variables > Actions**: add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
   `AWS_SESSION_TOKEN`.
6. Repo **Settings > Environments > New environment: `production`** > add yourself as *Required reviewer*
   (if your plan does not offer this on a private repo, delete the `environment:` line or make the repo public;
   say in the video that it is where you would add an approval).
7. Push to `main` (or run the **deploy** workflow). First deploy takes roughly 5-8 minutes.
8. Open the `LoadBalancerURL` output (CloudFormation console > Outputs, or the workflow summary).
9. **Credentials rotate every lab session.** Re-paste all three secrets at the start of every session or the
   deploy step fails with an expired-token error.
10. When finished: run the **destroy** workflow (or `scripts/teardown.sh`) to stop spend. Learner Lab budget is
    limited; do not leave the ALB running for days.

Fallback if GitHub Actions or the secrets approach misbehaves: `scripts/deploy_local.sh` runs the same steps
from your terminal. Weaker (no hosted CI), so only use it to avoid a zero.

## 4. Demonstration plan (20 minutes maximum)

Record the screen with voiceover (camera optional). Pre-run everything once so you know what to expect. The
stack creation and rolling updates take minutes: either narrate the theory while waiting, or speed up the
waiting in editing and say so on screen ("sped up 4x"). Check with your tutor that editing waits is fine.

| Time | Segment | Content |
|---|---|---|
| 0:00-1:30 | Intro and scope | Problem, what you built, why DevOps (CALMS), cite Kim et al. (2016) |
| 1:30-4:30 | Architecture | Walk the diagram; justify each component; Well-Architected pillars; trade-offs |
| 4:30-6:00 | Repo tour | `template.yaml`, workflows, tests; explain IaC and idempotence (Morris, 2020) |
| 6:00-6:45 | **Failing CI gate** | Push a commit with a failing test; show the pipeline blocked at the gate (shift-left) |
| 6:45-12:00 | **Clean deploy to a fresh environment** | Destroy first if needed, then push; show approval, build, S3 artefact, CloudFormation events creating VPC/ALB/ASG; open the URL; add a note |
| 12:00-14:30 | **Rolling update** | Change the page heading, push; show new version badge appearing while the app stays up; refresh to show different instance IDs |
| 14:30-16:00 | **Failure and rollback** | Push a deliberately broken startup (change `app:app` to `app:nope` in the template user data); show the signal failure and automatic rollback; app stays on the old version |
| 16:00-18:00 | Effectiveness assessment | Measured numbers (see section 5), strengths, weaknesses, DORA metrics |
| 18:00-19:30 | Reflection | What went wrong, credential weakness, what you would do in production, relevance to your organisation and industry |
| 19:30-20:00 | Close | Summary and next steps |

Keep total at about 19:30. Over 20 minutes you risk the last part not being marked.

## 5. Effectiveness assessment – evidence to collect during dry runs

Write these numbers down; vague claims score lower than measured ones.

- Pipeline duration (push to verified deployment), split by stage. Read it off the Actions run page.
- Lead time for change (commit to running in production) and deployment frequency (how many times you shipped).
- Change failure rate: count your broken deploys and how many were caught by the CI gate versus by
  rollback.
- Time to recover: how long the rollback took.
- Cost: look at Billing or the Learner Lab budget meter before and after.
- Security findings: Checkov results (typically no HTTPS, no ALB access logs, open ingress on port 80). State
  honestly which you accepted for the lab and what you would fix in production.

Honest weaknesses to discuss (this is what separates 70s from 80s): static credentials; single region; no
HTTPS or custom domain; no staging environment; in-memory state; rolling update is not blue/green; soft-fail
security scanning; no centralised logging or tracing; test suite is tiny.

## 6. Citations (spoken in the video + Harvard reference list)

Verify every entry (edition, publisher, year, pages) yourself before submitting. The brief says references
should be as close to the original source as possible: peer-reviewed papers and textbooks over blogs; vendor
documentation is acceptable only with awareness of its bias.

- Humble, J. and Farley, D. (2010) *Continuous Delivery*. Addison-Wesley.
- Kim, G., Humble, J., Debois, P. and Willis, J. (2016) *The DevOps Handbook*. IT Revolution Press.
- Forsgren, N., Humble, J. and Kim, G. (2018) *Accelerate*. IT Revolution Press.
- Morris, K. (2020) *Infrastructure as Code*. 2nd edn. O'Reilly.
- Bass, L., Weber, I. and Zhu, L. (2015) *DevOps: A Software Architect's Perspective*. Addison-Wesley.
- Leite, L. et al. (2019) 'A survey of DevOps concepts and challenges', *ACM Computing Surveys*, 52(6).
- Fitzgerald, B. and Stol, K.-J. (2017) 'Continuous software engineering: a roadmap and agenda', *Journal of
  Systems and Software*, 123.
- NIST (2022) *SP 800-218: Secure Software Development Framework (SSDF) v1.1*.
- DORA / Google Cloud, *Accelerate State of DevOps Report* (use the latest edition and cite its year).
- Amazon Web Services, *AWS Well-Architected Framework* (vendor documentation: acknowledge the bias).

## 7. Gen AI use

The brief's traffic light says constructive Gen AI use is appropriate. Be transparent about it: say briefly in the
video (and wherever your coversheet or module rules ask) that AI helped generate the app and pipeline code, and
that you reviewed, tested and can explain every part. If you cannot explain a line, read it until you can; the
marks are for your understanding, not the code.

## 8. Likely failure points

| Symptom | Likely cause | Fix |
|---|---|---|
| `ExpiredToken` / `InvalidClientTokenId` | Lab session rotated credentials | Re-paste the three secrets |
| `AccessDenied` creating a resource | Learner Lab restriction | Read the CloudFormation event reason; remove or swap that resource |
| Stack stuck creating, then rollback | Instances failed to signal (S3 access, pip install, wrong profile) | Check EC2 system log / `/var/log/cloud-init-output.log`; confirm `LabInstanceProfile` |
| Parameter `LatestAmiId` fails | SSM public parameter blocked | Replace with a hard-coded Amazon Linux 2023 AMI ID for us-east-1 |
| Drift step fails with permissions | Drift detection not allowed | Delete that step, mention it as a planned control |
| Approval step never appears | Environment reviewers not configured | See setup step 6 |
