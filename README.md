# Deploy MWAA DAGs to S3 (Manual Approve)

Workflow นี้ช่วยให้ **deploy DAGs ไปยัง S3 (MWAA)** ได้แบบ “ต้องมีคน approve ก่อน” โดยใช้การ **สร้าง Issue อัตโนมัติ** และรอคอมเมนต์คำสั่ง:

- อนุมัติ: พิมพ์คอมเมนต์ **`/approve`**
- ปฏิเสธ: พิมพ์คอมเมนต์ **`/reject`**

จากนั้นจึงค่อยทำ `aws s3 sync dags/ -> s3://<bucket>/dags/`

---

## โครงสร้าง Workflow

ไฟล์ตัวอย่าง (ที่คุณมี) ควรวางไว้ที่:

```
.github/workflows/deploy-dags-manual-approve.yml
```

มันทำงาน 3 job หลัก:

1) **request_approval**  
   สร้าง Issue เพื่อขออนุมัติ และส่งต่อ `issue_number` ไปยัง job ถัดไป

2) **wait_for_approval**  
   Poll ดูคอมเมนต์ใน Issue ทุก ๆ 15 วินาที (ปรับได้) จนกว่าจะเจอ `/approve` หรือ `/reject`  
   - ถ้า `/reject` -> workflow fail  
   - ถ้า `/approve` -> ไป job deploy

3) **deploy**  
   checkout โค้ด -> ตั้ง AWS credentials -> sync DAGs ไป S3

---

## วิธีติดตั้ง (Setup)

### 1) สร้าง Workflow File
วาง workflow ของคุณใน repo ตาม path นี้:

```
.github/workflows/deploy-dags-manual-approve.yml
```

> แนะนำให้ตั้งชื่อไฟล์ให้อ่านง่าย และหลีกเลี่ยงช่องว่าง

---

### 2) ตั้ง Secrets ใน GitHub

ไปที่: **Settings → Secrets and variables → Actions → New repository secret**

ต้องมีอย่างน้อย:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (เช่น `ap-southeast-1`)
- `MWAA_S3_BUCKET` (ชื่อ bucket ที่เก็บ DAGs)

> ถ้าอยากปลอดภัยกว่านี้ แนะนำใช้ OIDC + IAM Role (ไม่ต้องใช้ access key) แต่ตัวอย่างนี้ใช้ secrets ได้เลย

---

### 3) Permissions ที่ต้องมี

workflow ของคุณมี:

```yaml
permissions:
  contents: read
  issues: write
  actions: read
```

- `issues: write` จำเป็นสำหรับการสร้าง issue และอ่านคอมเมนต์
- `contents: read` ใช้สำหรับ checkout repo
- `actions: read` โดยมากไม่จำเป็นมากนัก แต่ใส่ไว้ก็ได้

---

### 4) ใครสามารถ Approve ได้?

โดยค่าเริ่มต้น **ใครที่คอมเมนต์ใน Issue ได้ ก็สามารถพิมพ์ `/approve` ได้**  
ดังนั้นคุณควรจำกัดสิทธิ์ให้คน approve เป็นกลุ่มที่เหมาะสม

วิธีนิยม:

- ตั้งค่า repo ให้ **เฉพาะ Collaborators/Team** ที่มีสิทธิ์ เขียน/คอมเมนต์ได้
- หรือปรับสคริปต์ให้ “ตรวจผู้ใช้” ว่าอยู่ใน allowlist / team ก่อนอนุมัติ (ดูหัวข้อด้านล่าง)

---

## วิธีใช้งาน

### Trigger โดย Push
เมื่อมีการ push เข้า `main` และมีการแก้ไฟล์ใน `dags/**`:

- Workflow จะรันอัตโนมัติ
- สร้าง Issue ใหม่เพื่อขออนุมัติ
- รอ `/approve` หรือ `/reject`

### Trigger แบบ Manual
ไปที่:

**Actions → Deploy DAGs to S3 (Manual Approve) → Run workflow**

---

## วิธี Approve / Reject

1) เปิด Issue ที่ workflow สร้างให้ (ลิงก์อยู่ใน logs ของ job `request_approval`)
2) คอมเมนต์ **ตรงตัว**:

- Approve:

```
/approve
```

- Reject:

```
/reject
```

> ต้องตรงตัว (มี slash และไม่มีข้อความอื่นต่อท้าย) เพราะสคริปต์ filter แบบ `===`

---

## ปรับ Timeout / Poll Interval

ใน job `wait_for_approval`:

```js
const timeoutMinutes = 60;   // ปรับได้
const pollSeconds    = 15;   // ปรับได้
```

- ถ้าอยากให้รอนานขึ้น ปรับ `timeoutMinutes`
- ถ้าอยากให้เช็คบ่อยขึ้น/น้อยลง ปรับ `pollSeconds`

---

## ความปลอดภัย (แนะนำ)

### A) จำกัดคน approve (Allowlist)

แนวคิด: ตรวจว่า `decision.user` อยู่ในรายชื่อที่อนุญาตก่อนรับ `/approve`

ตัวอย่าง (เพิ่มในสคริปต์):

```js
const allowed = ["your-admin-username", "team-lead-username"];

if (!allowed.includes(decision.user)) {
  core.notice(`Ignoring approval from @${decision.user} (not in allowlist)`);
  // แล้ววน loop ต่อเพื่อรอคนที่อนุญาต
  return null;
}
```

> ถ้าคุณอยากให้ผมแก้ workflow ให้แบบ allowlist หรือเช็คว่าอยู่ใน GitHub Team เดียวกัน บอกชื่อ team/org ได้

---

### B) แนะนำใช้ OIDC แทน Access Keys (Best practice)

- ลดความเสี่ยง secrets รั่ว
- ให้ GitHub Actions assume role ใน AWS ด้วย OIDC

ถ้าคุณอยากไปทางนี้ ผมทำตัวอย่าง IAM Role + trust policy + workflow ให้ได้

---

## Notes / Troubleshooting

- ถ้า workflow บอกหา `.github/DEPLOY_SHA` ไม่เจอ → ต้องสร้างโฟลเดอร์ก่อน (`mkdir -p .github`) หรืออย่าเขียนไฟล์ลง `.github/` ใน runtime  
- ถ้า `aws s3 sync` ล้มเหลว → ตรวจ `AWS_REGION`, bucket name, และสิทธิ์ IAM (ต้องมีอย่างน้อย `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` บน path dags)

---

## สรุป

- push หรือกด run workflow → สร้าง Issue ขออนุมัติ
- คนที่รับผิดชอบคอมเมนต์ `/approve` หรือ `/reject`
- ถ้า approve → deploy DAGs ไป S3 ทันที
