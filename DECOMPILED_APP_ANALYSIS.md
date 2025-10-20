# Comprehensive Analysis of Decompiled Apps - MX11 Features Discovery

**Analysis Date:** October 20, 2025  
**Target Apps:** Fun Print 6.09.16, RawBT  
**Objective:** Discover MX11-specific features, commands, and capabilities not yet implemented

---

## 📋 **Analysis Progress Tracker**

### ✅ **Completed Sections:**
- [x] Directory structure mapping
- [x] Fun Print 6.x AndroidManifest analysis
- [ ] Fun Print 6.x smali code analysis (BLE/printer related)
- [ ] Fun Print 6.x assets analysis (printer configs/data)
- [ ] RawBT app analysis
- [ ] Command comparison and gap analysis
- [ ] Battery status investigation
- [ ] Advanced features discovery

### 🔍 **Current Focus:** Searching for printer-specific smali code

---

## 🎯 **Key Investigation Areas**

### 1. **Battery Status Mystery**
- **Issue:** Current implementation doesn't return battery percentage
- **Question:** Is there a different command or parsing method?
- **Status:** 🔍 Investigating

### 2. **Advanced Commands Discovery**
- **Target:** Commands beyond basic V5G protocol
- **Focus:** MX11-specific optimizations
- **Status:** 🔍 Investigating

### 3. **Thermal Protection Logic**
- **Target:** Automatic concentration adjustment algorithms
- **Status:** 🔍 Investigating

---

## 📱 **Fun Print 6.09.16 Analysis**

### **App Structure Overview:**
- **Package:** com.fun.mxw
- **Version:** 6.09.16
- **Architecture:** Multi-dex with 4 smali classes directories
- **Key Directories:**
  - `smali/` - Main application code
  - `smali_classes2/` - Additional classes
  - `smali_classes3/` - More classes
  - `smali_classes4/` - Extended classes
  - `assets/` - Configuration files and data

### **AndroidManifest Analysis:**

#### **🔑 Key Permissions (Printer-Related):**
- `BLUETOOTH` - Basic Bluetooth access
- `BLUETOOTH_ADMIN` - Bluetooth device management
- `BLUETOOTH_SCAN` - Modern BLE scanning (Android 12+)
- `BLUETOOTH_CONNECT` - Modern BLE connection (Android 12+)
- `BLUETOOTH_PRIVILEGED` - **Advanced Bluetooth access** ⚠️
- `ACCESS_COARSE_LOCATION` / `ACCESS_FINE_LOCATION` - Required for BLE scanning
- `FOREGROUND_SERVICE` - Background printer operations

#### **🚨 Notable Findings:**
1. **BLUETOOTH_PRIVILEGED** - This is unusual and suggests advanced BLE capabilities
2. **Modern BLE permissions** - App supports Android 12+ BLE improvements
3. **Foreground service** - Can run printer operations in background
4. **No printer-specific services** visible in manifest (likely in smali code)

#### **📦 App Framework:**
- **DCloud/UniApp** - Cross-platform framework (HTML5/JS + Native)
- **Multi-process architecture** - Separate processes for different functions
- **Large heap enabled** - Can handle large image processing

### **Initial Observations:**
- Large multi-dex application (4 smali directories indicates >65k methods)
- Uses DCloud framework - printer logic likely in JavaScript + native bridges
- BLUETOOTH_PRIVILEGED suggests access to advanced BLE features
- Assets directory may contain printer configuration files

---

## 🔧 **RawBT Analysis**

### **App Structure Overview:**
- **Package:** ru.a402d.rawbtprinter
- **Focus:** Generic Bluetooth thermal printer support
- **Key Interest:** Universal printer compatibility approach

---

## 📝 **Findings Log**

### **Memory Update 1:** Initial Structure Analysis Complete
- Mapped directory structures for both apps
- Identified key areas for investigation
- Ready to begin detailed code analysis

### **Memory Update 3:** DCloud Framework Discovery
- **Critical Finding:** Fun Print 6.x is built with DCloud/UniApp framework
- **Architecture:** HTML5/JavaScript + Native bridges
- **Main app code location:** `/assets/apps/__UNI__573AE67/www/` (JavaScript files)
- **Native code:** Minimal - mostly in smali directories as framework code
- **Implication:** Printer logic likely in JavaScript files, not smali

**Key Observations:**
- App uses extensive third-party libraries (Glide, FastJSON, ByteDance SDK, etc.)
- Main business logic in JavaScript rather than native Android code
- Need to examine JavaScript files in assets for printer protocols

**Next Steps:**
1. Examine JavaScript files in main app directory
2. Search for printer/BLE related JavaScript code
3. Look for MX11, V5G, or printer model references in JS
4. Check for battery status handling in JavaScript

---

## ❓ **Questions for Tomorrow's Discussion**

1. **BLUETOOTH_PRIVILEGED:** What advanced BLE features does this enable?
2. **Battery Status:** Why no percentage in current implementation?
3. **Command Discovery:** What advanced commands are we missing?
4. **DCloud Framework:** How does JS-native bridge work for printer control?

---

**Analysis Status:** 🟡 In Progress - Starting smali code examination
