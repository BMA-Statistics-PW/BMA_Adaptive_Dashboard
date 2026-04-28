# BMA Adaptive Signaling Pilot Dashboard

แดชบอร์ดแบบ static สำหรับ GitHub Pages เพื่อสรุปผลโครงการนำร่อง Adaptive Signaling ของกรุงเทพมหานคร โดยหน้าเว็บโหลดข้อมูลจริงจากไฟล์ในรีโพและรองรับการ drill-down รายทางแยกผ่าน dropdown

## Live Site

https://bma-statistics-pw.github.io/BMA_Adaptive_Dashboard/

## Dataset in Repository

ไฟล์ข้อมูลถูก generate จาก workbook ต้นทางและเก็บไว้ในโฟลเดอร์ `data/`

- `data/Daily_Stats.csv`
- `data/Hourly_Heatmap.csv`
- `data/Junction_Ranking.csv`
- `data/dashboard-data.js`

`dashboard-data.js` เป็น payload ที่หน้าเว็บใช้โดยตรง ส่วน CSV เก็บไว้เพื่ออ้างอิงและตรวจสอบย้อนหลังใน GitHub

## Regenerate Data

รันคำสั่งนี้จาก root ของรีโพ

```bash
python scripts/generate_dashboard_data.py "D:\Adaptive_Volume\_Merged\Statistics_Summary.xlsx"
```

สคริปต์จะ export CSV ทั้ง 3 ชุดและสร้าง `data/dashboard-data.js` ใหม่ให้ตรงกับ workbook ต้นทาง

## Dashboard Features

- ภาพรวม KPI แยก Weekday, Weekend และสงกรานต์
- กราฟ Hourly Delay Trend สำหรับภาพรวมทั้งระบบ
- Dropdown เลือกดูข้อมูลรายทางแยกทั้ง 73 จุด
- KPI และกราฟรายชั่วโมงอัปเดตตามทางแยกที่เลือก
- ข้อมูล rank และ average daily volume ของทางแยกที่เลือก

## Tech Stack

- HTML5
- CSS3
- Vanilla JavaScript
- Chart.js
- GitHub Pages

## Source Workbook

- Workbook: `D:\Adaptive_Volume\_Merged\Statistics_Summary.xlsx`
- Sheets used: `Daily_Stats`, `Hourly_Heatmap`, `Junction_Ranking`

## Notes

- รีโพนี้ deploy ได้จากไฟล์ static บน branch `main`
- หาก workbook เปลี่ยน ให้ regenerate data แล้ว commit/push ใหม่เพื่ออัปเดตหน้าเว็บ
