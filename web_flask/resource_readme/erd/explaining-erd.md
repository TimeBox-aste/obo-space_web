# Explaining ERD
---

### **Database Overview:**
The database is designed for a **Server Sharing** system, where users share copies, and notifications are managed. The diagram consists of **four tables**:  
1. `user_data`  
2. `copy_shared`  
3. `notifications`  
4. `statuses`  

These tables are interconnected through **Primary Keys (PK)** and **Foreign Keys (FK)**.

---

### **Tables and Relationships:**

1. **user_data**  
   - **Primary Key (PK):** `id`  
   - **Attributes:**  
     - `email`  
     - `nickname`  
   - **Description:**  
     This table stores the user details like email and nickname.  

2. **copy_shared**  
   - **Primary Key (PK):** `id`  
   - **Foreign Key (FK):** `id_user` → **user_data.id**  
   - **Attributes:**  
     - `dt_created` (date-time when the file copy was created)  
     - `name_file_uuid` (a unique identifier for the shared file name)  
   - **Description:**  
     This table stores information about files that have been shared by users. The `id_user` field links to the `user_data` table to associate file sharing with a user.  

3. **notifications**  
   - **Primary Key (PK):** `uniqueId`  
   - **Foreign Keys (FK):**  
     - `id_copy_shared` → **copy_shared.id**  
     - `id_status_sending` → **statuses.id**  
   - **Attributes:**  
     - `dt_sent` (date-time when the notification was sent)  
   - **Description:**  
     This table manages notifications, linking to a shared copy (`copy_shared`) and a status (`statuses`).  

4. **statuses**  
   - **Primary Key (PK):** `id`  
   - **Attributes:**  
     - `name` (status name)  
   - **Description:**  
     This table holds the various statuses that can be assigned to notifications.  

---

### **Relationships Between Tables:**

1. `user_data` → `copy_shared`  
   - One-to-Many relationship: A user can share multiple file copies.  

2. `copy_shared` → `notifications`  
   - One-to-Many relationship: Each shared file can have multiple notifications.  

3. `statuses` → `notifications`  
   - One-to-Many relationship: A status can apply to multiple notifications.  

---

### **Example Usage:**
- A user (`user_data`) shares a file (`copy_shared`) at a particular time (`dt_created`).
- The system generates a notification (`notifications`) for the file, associating a specific status (`statuses`).
- Notifications are timestamped (`dt_sent`) to indicate when they were sent.
