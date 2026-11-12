import Foundation

// MARK: - Apple Device Master Model & Silicon Specifications

public enum AppleDeviceCategory: String, Codable, CaseIterable {
    case iphone = "iPhone"
    case ipad = "iPad"
    case ipod = "iPod touch"
    case watch = "Apple Watch"
    case appleTv = "Apple TV"
}

public struct AppleDeviceProfile: Identifiable, Codable {
    public var id: String { identifier }
    public let identifier: String        // e.g. "iPad6,7", "iPhone15,2"
    public let cpid: String              // e.g. "0x8001", "0x8120"
    public let bdid: String              // e.g. "0x10", "0x02"
    public let marketingName: String      // e.g. "iPad Pro 12.9-inch (1st generation)"
    public let socName: String            // e.g. "Apple A9X"
    public let boardConfig: String        // e.g. "j98aap", "d84ap"
    public let category: AppleDeviceCategory
    public let latestSignedVersion: String // e.g. "16.7.16", "18.3.1"
    public let defaultIpswPattern: String  // e.g. "iPadPro_12.9_16.7.16_20H392_Restore.ipsw"

    public var formattedSummary: String {
        "\(marketingName) [\(identifier)] · \(socName) (CPID: \(cpid) · BDID: \(bdid))"
    }
}

// MARK: - Comprehensive Apple Device Master Registry (All iPhones & iPads)

public struct AppleDeviceMasterRegistry {
    public static let allDevices: [AppleDeviceProfile] = [
        // MARK: iPad Pro 13-inch & 11-inch (M4)
        AppleDeviceProfile(identifier: "iPad16,5", cpid: "0x8132", bdid: "0x02", marketingName: "iPad Pro 13-inch (M4, Wi-Fi)", socName: "Apple M4", boardConfig: "j720ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_13.0_M4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad16,6", cpid: "0x8132", bdid: "0x04", marketingName: "iPad Pro 13-inch (M4, Cellular)", socName: "Apple M4", boardConfig: "j721ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_13.0_M4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad16,3", cpid: "0x8132", bdid: "0x06", marketingName: "iPad Pro 11-inch (M4, Wi-Fi)", socName: "Apple M4", boardConfig: "j717ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_11.0_M4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad16,4", cpid: "0x8132", bdid: "0x08", marketingName: "iPad Pro 11-inch (M4, Cellular)", socName: "Apple M4", boardConfig: "j718ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_11.0_M4_Restore.ipsw"),

        // MARK: iPad Air 13-inch & 11-inch (M2)
        AppleDeviceProfile(identifier: "iPad14,10", cpid: "0x8112", bdid: "0x0A", marketingName: "iPad Air 13-inch (M2, Wi-Fi)", socName: "Apple M2", boardConfig: "j537ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_13.0_M2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,11", cpid: "0x8112", bdid: "0x0C", marketingName: "iPad Air 13-inch (M2, Cellular)", socName: "Apple M2", boardConfig: "j538ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_13.0_M2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,8", cpid: "0x8112", bdid: "0x06", marketingName: "iPad Air 11-inch (M2, Wi-Fi)", socName: "Apple M2", boardConfig: "j507ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_11.0_M2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,9", cpid: "0x8112", bdid: "0x08", marketingName: "iPad Air 11-inch (M2, Cellular)", socName: "Apple M2", boardConfig: "j508ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_11.0_M2_Restore.ipsw"),

        // MARK: iPad Pro 12.9-inch & 11-inch (6th & 4th gen M2)
        AppleDeviceProfile(identifier: "iPad14,5", cpid: "0x8112", bdid: "0x02", marketingName: "iPad Pro 12.9-inch (6th gen M2, Wi-Fi)", socName: "Apple M2", boardConfig: "j620ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_6th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,6", cpid: "0x8112", bdid: "0x04", marketingName: "iPad Pro 12.9-inch (6th gen M2, Cellular)", socName: "Apple M2", boardConfig: "j621ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_6th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,3", cpid: "0x8112", bdid: "0x00", marketingName: "iPad Pro 11-inch (4th gen M2, Wi-Fi)", socName: "Apple M2", boardConfig: "j617ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_4th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,4", cpid: "0x8112", bdid: "0x01", marketingName: "iPad Pro 11-inch (4th gen M2, Cellular)", socName: "Apple M2", boardConfig: "j618ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_4th_Restore.ipsw"),

        // MARK: iPad Pro 12.9-inch & 11-inch (5th & 3rd gen M1)
        AppleDeviceProfile(identifier: "iPad13,8", cpid: "0x8103", bdid: "0x02", marketingName: "iPad Pro 12.9-inch (5th gen M1, Wi-Fi)", socName: "Apple M1", boardConfig: "j522ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_5th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad13,9", cpid: "0x8103", bdid: "0x04", marketingName: "iPad Pro 12.9-inch (5th gen M1, Cellular)", socName: "Apple M1", boardConfig: "j523ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_5th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad13,4", cpid: "0x8103", bdid: "0x00", marketingName: "iPad Pro 11-inch (3rd gen M1, Wi-Fi)", socName: "Apple M1", boardConfig: "j517ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_3rd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad13,5", cpid: "0x8103", bdid: "0x01", marketingName: "iPad Pro 11-inch (3rd gen M1, Cellular)", socName: "Apple M1", boardConfig: "j518ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_3rd_Restore.ipsw"),

        // MARK: iPad Air (5th gen M1) & (4th gen A14)
        AppleDeviceProfile(identifier: "iPad13,16", cpid: "0x8103", bdid: "0x06", marketingName: "iPad Air (5th gen M1, Wi-Fi)", socName: "Apple M1", boardConfig: "j407ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_5th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad13,17", cpid: "0x8103", bdid: "0x08", marketingName: "iPad Air (5th gen M1, Cellular)", socName: "Apple M1", boardConfig: "j408ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_5th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad13,1", cpid: "0x8101", bdid: "0x00", marketingName: "iPad Air (4th gen, Wi-Fi)", socName: "Apple A14 Bionic", boardConfig: "j307ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_4th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad13,2", cpid: "0x8101", bdid: "0x02", marketingName: "iPad Air (4th gen, Cellular)", socName: "Apple A14 Bionic", boardConfig: "j308ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir_4th_Restore.ipsw"),

        // MARK: iPad (10th, 9th, 8th, 7th, 6th, 5th gen)
        AppleDeviceProfile(identifier: "iPad13,18", cpid: "0x8101", bdid: "0x04", marketingName: "iPad (10th generation, Wi-Fi)", socName: "Apple A14 Bionic", boardConfig: "j271ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_10th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad13,19", cpid: "0x8101", bdid: "0x06", marketingName: "iPad (10th generation, Cellular)", socName: "Apple A14 Bionic", boardConfig: "j272ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_10th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad12,1", cpid: "0x8030", bdid: "0x00", marketingName: "iPad (9th generation, Wi-Fi)", socName: "Apple A13 Bionic", boardConfig: "j181ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_9th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad12,2", cpid: "0x8030", bdid: "0x02", marketingName: "iPad (9th generation, Cellular)", socName: "Apple A13 Bionic", boardConfig: "j182ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_9th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad11,6", cpid: "0x8020", bdid: "0x02", marketingName: "iPad (8th generation, Wi-Fi)", socName: "Apple A12 Bionic", boardConfig: "j171ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_8th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad11,7", cpid: "0x8020", bdid: "0x04", marketingName: "iPad (8th generation, Cellular)", socName: "Apple A12 Bionic", boardConfig: "j172ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_8th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,11", cpid: "0x8010", bdid: "0x12", marketingName: "iPad (7th generation, Wi-Fi)", socName: "Apple A10 Fusion", boardConfig: "j171ap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPad_7th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,12", cpid: "0x8010", bdid: "0x14", marketingName: "iPad (7th generation, Cellular)", socName: "Apple A10 Fusion", boardConfig: "j172ap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPad_7th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,5", cpid: "0x8010", bdid: "0x0C", marketingName: "iPad (6th generation, Wi-Fi)", socName: "Apple A10 Fusion", boardConfig: "j71bap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPad_6th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,6", cpid: "0x8010", bdid: "0x0E", marketingName: "iPad (6th generation, Cellular)", socName: "Apple A10 Fusion", boardConfig: "j72bap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPad_6th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad6,11", cpid: "0x8000", bdid: "0x08", marketingName: "iPad (5th generation, Wi-Fi)", socName: "Apple A9", boardConfig: "j71sap", category: .ipad, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPad_5th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad6,12", cpid: "0x8000", bdid: "0x0A", marketingName: "iPad (5th generation, Cellular)", socName: "Apple A9", boardConfig: "j72sap", category: .ipad, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPad_5th_Restore.ipsw"),

        // MARK: iPad mini (7th A17 Pro, 6th, 5th, 4th)
        AppleDeviceProfile(identifier: "iPad16,1", cpid: "0x8130", bdid: "0x00", marketingName: "iPad mini (A17 Pro, Wi-Fi)", socName: "Apple A17 Pro", boardConfig: "j410ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadmini_A17Pro_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad16,2", cpid: "0x8130", bdid: "0x02", marketingName: "iPad mini (A17 Pro, Cellular)", socName: "Apple A17 Pro", boardConfig: "j411ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadmini_A17Pro_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,1", cpid: "0x8110", bdid: "0x00", marketingName: "iPad mini (6th generation, Wi-Fi)", socName: "Apple A15 Bionic", boardConfig: "j310ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadmini_6th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad14,2", cpid: "0x8110", bdid: "0x02", marketingName: "iPad mini (6th generation, Cellular)", socName: "Apple A15 Bionic", boardConfig: "j311ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadmini_6th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad11,1", cpid: "0x8020", bdid: "0x06", marketingName: "iPad mini (5th generation, Wi-Fi)", socName: "Apple A12 Bionic", boardConfig: "j210ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadmini_5th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad11,2", cpid: "0x8020", bdid: "0x08", marketingName: "iPad mini (5th generation, Cellular)", socName: "Apple A12 Bionic", boardConfig: "j211ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadmini_5th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad5,1", cpid: "0x7000", bdid: "0x00", marketingName: "iPad mini 4 (Wi-Fi)", socName: "Apple A8", boardConfig: "j96ap", category: .ipad, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPadmini4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad5,2", cpid: "0x7000", bdid: "0x02", marketingName: "iPad mini 4 (Cellular)", socName: "Apple A8", boardConfig: "j97ap", category: .ipad, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPadmini4_Restore.ipsw"),

        // MARK: iPad Pro 12.9-inch (1st generation - Bench Target!), 9.7-inch, 10.5-inch, 2nd, 3rd, 4th gen
        AppleDeviceProfile(identifier: "iPad6,7", cpid: "0x8001", bdid: "0x10", marketingName: "iPad Pro 12.9-inch (1st gen, Wi-Fi)", socName: "Apple A9X", boardConfig: "j98aap", category: .ipad, latestSignedVersion: "16.7.16", defaultIpswPattern: "iPadPro_12.9_16.7.16_20H392_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad6,8", cpid: "0x8001", bdid: "0x12", marketingName: "iPad Pro 12.9-inch (1st gen, Cellular)", socName: "Apple A9X", boardConfig: "j99aap", category: .ipad, latestSignedVersion: "16.7.16", defaultIpswPattern: "iPadPro_12.9_16.7.16_20H392_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad6,3", cpid: "0x8001", bdid: "0x02", marketingName: "iPad Pro 9.7-inch (Wi-Fi)", socName: "Apple A9X", boardConfig: "j127ap", category: .ipad, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPadPro_9.7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad6,4", cpid: "0x8001", bdid: "0x04", marketingName: "iPad Pro 9.7-inch (Cellular)", socName: "Apple A9X", boardConfig: "j128ap", category: .ipad, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPadPro_9.7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,1", cpid: "0x8011", bdid: "0x0C", marketingName: "iPad Pro 12.9-inch (2nd gen, Wi-Fi)", socName: "Apple A10X Fusion", boardConfig: "j120ap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPadPro_12.9_2nd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,2", cpid: "0x8011", bdid: "0x0E", marketingName: "iPad Pro 12.9-inch (2nd gen, Cellular)", socName: "Apple A10X Fusion", boardConfig: "j121ap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPadPro_12.9_2nd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,3", cpid: "0x8011", bdid: "0x04", marketingName: "iPad Pro 10.5-inch (Wi-Fi)", socName: "Apple A10X Fusion", boardConfig: "j207ap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPadPro_10.5_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad7,4", cpid: "0x8011", bdid: "0x06", marketingName: "iPad Pro 10.5-inch (Cellular)", socName: "Apple A10X Fusion", boardConfig: "j208ap", category: .ipad, latestSignedVersion: "17.7.5", defaultIpswPattern: "iPadPro_10.5_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,5", cpid: "0x8027", bdid: "0x08", marketingName: "iPad Pro 12.9-inch (3rd gen, Wi-Fi)", socName: "Apple A12X Bionic", boardConfig: "j320ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_3rd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,6", cpid: "0x8027", bdid: "0x0A", marketingName: "iPad Pro 12.9-inch (3rd gen, 1TB Wi-Fi)", socName: "Apple A12X Bionic", boardConfig: "j320ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_3rd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,7", cpid: "0x8027", bdid: "0x0C", marketingName: "iPad Pro 12.9-inch (3rd gen, Cellular)", socName: "Apple A12X Bionic", boardConfig: "j321ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_3rd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,8", cpid: "0x8027", bdid: "0x0E", marketingName: "iPad Pro 12.9-inch (3rd gen, 1TB Cellular)", socName: "Apple A12X Bionic", boardConfig: "j321ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_3rd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,1", cpid: "0x8027", bdid: "0x00", marketingName: "iPad Pro 11-inch (1st gen, Wi-Fi)", socName: "Apple A12X Bionic", boardConfig: "j317ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_1st_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,2", cpid: "0x8027", bdid: "0x02", marketingName: "iPad Pro 11-inch (1st gen, 1TB Wi-Fi)", socName: "Apple A12X Bionic", boardConfig: "j317ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_1st_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,3", cpid: "0x8027", bdid: "0x04", marketingName: "iPad Pro 11-inch (1st gen, Cellular)", socName: "Apple A12X Bionic", boardConfig: "j318ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_1st_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,4", cpid: "0x8027", bdid: "0x06", marketingName: "iPad Pro 11-inch (1st gen, 1TB Cellular)", socName: "Apple A12X Bionic", boardConfig: "j318ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_1st_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,11", cpid: "0x8027", bdid: "0x12", marketingName: "iPad Pro 12.9-inch (4th gen, Wi-Fi)", socName: "Apple A12Z Bionic", boardConfig: "j420ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_4th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,12", cpid: "0x8027", bdid: "0x14", marketingName: "iPad Pro 12.9-inch (4th gen, Cellular)", socName: "Apple A12Z Bionic", boardConfig: "j421ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_12.9_4th_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,9", cpid: "0x8027", bdid: "0x10", marketingName: "iPad Pro 11-inch (2nd gen, Wi-Fi)", socName: "Apple A12Z Bionic", boardConfig: "j417ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_2nd_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad8,10", cpid: "0x8027", bdid: "0x11", marketingName: "iPad Pro 11-inch (2nd gen, Cellular)", socName: "Apple A12Z Bionic", boardConfig: "j418ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadPro_11_2nd_Restore.ipsw"),

        // MARK: iPhone 16 Series
        AppleDeviceProfile(identifier: "iPhone17,1", cpid: "0x8142", bdid: "0x02", marketingName: "iPhone 16 Pro", socName: "Apple A18 Pro", boardConfig: "d93ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone17,1_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone17,2", cpid: "0x8142", bdid: "0x04", marketingName: "iPhone 16 Pro Max", socName: "Apple A18 Pro", boardConfig: "d94ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone17,2_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone17,3", cpid: "0x8140", bdid: "0x00", marketingName: "iPhone 16", socName: "Apple A18", boardConfig: "d47ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone17,3_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone17,4", cpid: "0x8140", bdid: "0x02", marketingName: "iPhone 16 Plus", socName: "Apple A18", boardConfig: "d48ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone17,4_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone17,5", cpid: "0x8140", bdid: "0x04", marketingName: "iPhone 16e", socName: "Apple A18", boardConfig: "d49ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone17,5_18.3.1_Restore.ipsw"),

        // MARK: iPhone 15 Series
        AppleDeviceProfile(identifier: "iPhone16,1", cpid: "0x8130", bdid: "0x00", marketingName: "iPhone 15 Pro", socName: "Apple A17 Pro", boardConfig: "d83ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone16,1_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone16,2", cpid: "0x8130", bdid: "0x02", marketingName: "iPhone 15 Pro Max", socName: "Apple A17 Pro", boardConfig: "d84ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone16,2_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone15,4", cpid: "0x8120", bdid: "0x00", marketingName: "iPhone 15", socName: "Apple A16 Bionic", boardConfig: "d37ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone15,4_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone15,5", cpid: "0x8120", bdid: "0x02", marketingName: "iPhone 15 Plus", socName: "Apple A16 Bionic", boardConfig: "d38ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone15,5_18.3.1_Restore.ipsw"),

        // MARK: iPhone 14 Series
        AppleDeviceProfile(identifier: "iPhone15,2", cpid: "0x8120", bdid: "0x04", marketingName: "iPhone 14 Pro", socName: "Apple A16 Bionic", boardConfig: "d73ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone15,2_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone15,3", cpid: "0x8120", bdid: "0x06", marketingName: "iPhone 14 Pro Max", socName: "Apple A16 Bionic", boardConfig: "d74ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone15,3_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone14,7", cpid: "0x8110", bdid: "0x06", marketingName: "iPhone 14", socName: "Apple A15 Bionic", boardConfig: "d27ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone14,7_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone14,8", cpid: "0x8110", bdid: "0x08", marketingName: "iPhone 14 Plus", socName: "Apple A15 Bionic", boardConfig: "d28ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone14,8_18.3.1_Restore.ipsw"),

        // MARK: iPhone 13 Series & SE 3
        AppleDeviceProfile(identifier: "iPhone14,2", cpid: "0x8110", bdid: "0x02", marketingName: "iPhone 13 Pro", socName: "Apple A15 Bionic", boardConfig: "d63ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone14,2_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone14,3", cpid: "0x8110", bdid: "0x04", marketingName: "iPhone 13 Pro Max", socName: "Apple A15 Bionic", boardConfig: "d64ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone14,3_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone14,4", cpid: "0x8110", bdid: "0x00", marketingName: "iPhone 13 mini", socName: "Apple A15 Bionic", boardConfig: "d16ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone14,4_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone14,5", cpid: "0x8110", bdid: "0x01", marketingName: "iPhone 13", socName: "Apple A15 Bionic", boardConfig: "d17ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone14,5_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone14,6", cpid: "0x8110", bdid: "0x0A", marketingName: "iPhone SE (3rd generation)", socName: "Apple A15 Bionic", boardConfig: "d49ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone14,6_18.3.1_Restore.ipsw"),

        // MARK: iPhone 12 Series
        AppleDeviceProfile(identifier: "iPhone13,1", cpid: "0x8101", bdid: "0x00", marketingName: "iPhone 12 mini", socName: "Apple A14 Bionic", boardConfig: "d52gap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone13,1_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone13,2", cpid: "0x8101", bdid: "0x02", marketingName: "iPhone 12", socName: "Apple A14 Bionic", boardConfig: "d53gap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone13,2_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone13,3", cpid: "0x8101", bdid: "0x04", marketingName: "iPhone 12 Pro", socName: "Apple A14 Bionic", boardConfig: "d53pap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone13,3_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone13,4", cpid: "0x8101", bdid: "0x06", marketingName: "iPhone 12 Pro Max", socName: "Apple A14 Bionic", boardConfig: "d54pap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone13,4_18.3.1_Restore.ipsw"),

        // MARK: iPhone 11 Series & SE 2
        AppleDeviceProfile(identifier: "iPhone12,1", cpid: "0x8030", bdid: "0x00", marketingName: "iPhone 11", socName: "Apple A13 Bionic", boardConfig: "n104ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone12,1_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone12,3", cpid: "0x8030", bdid: "0x02", marketingName: "iPhone 11 Pro", socName: "Apple A13 Bionic", boardConfig: "d421ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone12,3_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone12,5", cpid: "0x8030", bdid: "0x04", marketingName: "iPhone 11 Pro Max", socName: "Apple A13 Bionic", boardConfig: "d431ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone12,5_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone12,8", cpid: "0x8030", bdid: "0x08", marketingName: "iPhone SE (2nd generation)", socName: "Apple A13 Bionic", boardConfig: "d79ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone12,8_18.3.1_Restore.ipsw"),

        // MARK: iPhone XS, XR, X, 8, 7, 6s
        AppleDeviceProfile(identifier: "iPhone11,2", cpid: "0x8020", bdid: "0x00", marketingName: "iPhone XS", socName: "Apple A12 Bionic", boardConfig: "d321ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone11,2_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone11,4", cpid: "0x8020", bdid: "0x02", marketingName: "iPhone XS Max (China)", socName: "Apple A12 Bionic", boardConfig: "d331pap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone11,4_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone11,6", cpid: "0x8020", bdid: "0x04", marketingName: "iPhone XS Max", socName: "Apple A12 Bionic", boardConfig: "d331ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone11,6_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone11,8", cpid: "0x8020", bdid: "0x06", marketingName: "iPhone XR", socName: "Apple A12 Bionic", boardConfig: "n841ap", category: .iphone, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPhone11,8_18.3.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone10,3", cpid: "0x8015", bdid: "0x00", marketingName: "iPhone X (GSM/CDMA)", socName: "Apple A11 Bionic", boardConfig: "d22ap", category: .iphone, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPhone10,3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone10,6", cpid: "0x8015", bdid: "0x02", marketingName: "iPhone X (GSM)", socName: "Apple A11 Bionic", boardConfig: "d221ap", category: .iphone, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPhone10,6_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone10,1", cpid: "0x8015", bdid: "0x04", marketingName: "iPhone 8 (Global)", socName: "Apple A11 Bionic", boardConfig: "d20ap", category: .iphone, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPhone10,1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone10,4", cpid: "0x8015", bdid: "0x06", marketingName: "iPhone 8 (GSM)", socName: "Apple A11 Bionic", boardConfig: "d201ap", category: .iphone, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPhone10,4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone10,2", cpid: "0x8015", bdid: "0x08", marketingName: "iPhone 8 Plus (Global)", socName: "Apple A11 Bionic", boardConfig: "d21ap", category: .iphone, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPhone10,2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone10,5", cpid: "0x8015", bdid: "0x0A", marketingName: "iPhone 8 Plus (GSM)", socName: "Apple A11 Bionic", boardConfig: "d211ap", category: .iphone, latestSignedVersion: "16.7.10", defaultIpswPattern: "iPhone10,5_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone9,1", cpid: "0x8010", bdid: "0x00", marketingName: "iPhone 7 (Global)", socName: "Apple A10 Fusion", boardConfig: "d10ap", category: .iphone, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPhone_4.7_P3_15.8.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone9,3", cpid: "0x8010", bdid: "0x02", marketingName: "iPhone 7 (GSM)", socName: "Apple A10 Fusion", boardConfig: "d101ap", category: .iphone, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPhone_4.7_P3_15.8.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone9,2", cpid: "0x8010", bdid: "0x04", marketingName: "iPhone 7 Plus (Global)", socName: "Apple A10 Fusion", boardConfig: "d11ap", category: .iphone, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPhone_5.5_P3_15.8.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone9,4", cpid: "0x8010", bdid: "0x06", marketingName: "iPhone 7 Plus (GSM)", socName: "Apple A10 Fusion", boardConfig: "d111ap", category: .iphone, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPhone_5.5_P3_15.8.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone8,1", cpid: "0x8000", bdid: "0x00", marketingName: "iPhone 6s", socName: "Apple A9", boardConfig: "n71map", category: .iphone, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPhone_4.7_15.8.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone8,2", cpid: "0x8000", bdid: "0x04", marketingName: "iPhone 6s Plus", socName: "Apple A9", boardConfig: "n66map", category: .iphone, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPhone_5.5_15.8.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone8,4", cpid: "0x8000", bdid: "0x02", marketingName: "iPhone SE (1st generation)", socName: "Apple A9", boardConfig: "n69ap", category: .iphone, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPhone_4.0_64bit_15.8.3_Restore.ipsw"),

        // MARK: Legacy iPhones (iPhone 6, 5s, 5c, 5, 4s, 4, 3GS, 3G, 2G)
        AppleDeviceProfile(identifier: "iPhone7,2", cpid: "0x7000", bdid: "0x06", marketingName: "iPhone 6", socName: "Apple A8", boardConfig: "n61ap", category: .iphone, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPhone_4.7_12.5.7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone7,1", cpid: "0x7000", bdid: "0x00", marketingName: "iPhone 6 Plus", socName: "Apple A8", boardConfig: "n56ap", category: .iphone, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPhone_5.5_12.5.7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone6,1", cpid: "0x8960", bdid: "0x00", marketingName: "iPhone 5s (GSM)", socName: "Apple A7", boardConfig: "n51ap", category: .iphone, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPhone_4.0_64bit_12.5.7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone6,2", cpid: "0x8960", bdid: "0x02", marketingName: "iPhone 5s (Global)", socName: "Apple A7", boardConfig: "n53ap", category: .iphone, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPhone_4.0_64bit_12.5.7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone5,3", cpid: "0x8950", bdid: "0x0A", marketingName: "iPhone 5c (GSM)", socName: "Apple A6", boardConfig: "n48ap", category: .iphone, latestSignedVersion: "10.3.3", defaultIpswPattern: "iPhone_4.0_32bit_10.3.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone5,4", cpid: "0x8950", bdid: "0x0E", marketingName: "iPhone 5c (Global)", socName: "Apple A6", boardConfig: "n49ap", category: .iphone, latestSignedVersion: "10.3.3", defaultIpswPattern: "iPhone_4.0_32bit_10.3.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone5,1", cpid: "0x8950", bdid: "0x00", marketingName: "iPhone 5 (GSM)", socName: "Apple A6", boardConfig: "n41ap", category: .iphone, latestSignedVersion: "10.3.4", defaultIpswPattern: "iPhone_4.0_32bit_10.3.4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone5,2", cpid: "0x8950", bdid: "0x02", marketingName: "iPhone 5 (Global)", socName: "Apple A6", boardConfig: "n42ap", category: .iphone, latestSignedVersion: "10.3.4", defaultIpswPattern: "iPhone_4.0_32bit_10.3.4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone4,1", cpid: "0x8940", bdid: "0x08", marketingName: "iPhone 4s", socName: "Apple A5", boardConfig: "n94ap", category: .iphone, latestSignedVersion: "9.3.6", defaultIpswPattern: "iPhone4,1_9.3.6_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone3,1", cpid: "0x8930", bdid: "0x00", marketingName: "iPhone 4 (GSM)", socName: "Apple A4", boardConfig: "n90ap", category: .iphone, latestSignedVersion: "7.1.2", defaultIpswPattern: "iPhone3,1_7.1.2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone3,2", cpid: "0x8930", bdid: "0x04", marketingName: "iPhone 4 (GSM Rev A)", socName: "Apple A4", boardConfig: "n90bap", category: .iphone, latestSignedVersion: "7.1.2", defaultIpswPattern: "iPhone3,2_7.1.2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone3,3", cpid: "0x8930", bdid: "0x06", marketingName: "iPhone 4 (CDMA)", socName: "Apple A4", boardConfig: "n92ap", category: .iphone, latestSignedVersion: "7.1.2", defaultIpswPattern: "iPhone3,3_7.1.2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone2,1", cpid: "0x8920", bdid: "0x00", marketingName: "iPhone 3GS", socName: "Samsung S5L8920", boardConfig: "n88ap", category: .iphone, latestSignedVersion: "6.1.6", defaultIpswPattern: "iPhone2,1_6.1.6_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone1,2", cpid: "0x8900", bdid: "0x00", marketingName: "iPhone 3G", socName: "Samsung S5L8900", boardConfig: "n82ap", category: .iphone, latestSignedVersion: "4.2.1", defaultIpswPattern: "iPhone1,2_4.2.1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPhone1,1", cpid: "0x8900", bdid: "0x00", marketingName: "iPhone 1st Gen (2G)", socName: "Samsung S5L8900", boardConfig: "m68ap", category: .iphone, latestSignedVersion: "3.1.3", defaultIpswPattern: "iPhone1,1_3.1.3_Restore.ipsw"),

        // MARK: Legacy iPads (iPad Air 1-3, iPad mini 1-3, iPad 1-4)
        AppleDeviceProfile(identifier: "iPad11,3", cpid: "0x8020", bdid: "0x0E", marketingName: "iPad Air (3rd gen, Wi-Fi)", socName: "Apple A12 Bionic", boardConfig: "j217ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad11,4", cpid: "0x8020", bdid: "0x10", marketingName: "iPad Air (3rd gen, Cellular)", socName: "Apple A12 Bionic", boardConfig: "j218ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPadAir3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad5,3", cpid: "0x7001", bdid: "0x02", marketingName: "iPad Air 2 (Wi-Fi)", socName: "Apple A8X", boardConfig: "j81ap", category: .ipad, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPadAir2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad5,4", cpid: "0x7001", bdid: "0x04", marketingName: "iPad Air 2 (Cellular)", socName: "Apple A8X", boardConfig: "j82ap", category: .ipad, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPadAir2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,1", cpid: "0x8960", bdid: "0x10", marketingName: "iPad Air (Wi-Fi)", socName: "Apple A7", boardConfig: "j71ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,2", cpid: "0x8960", bdid: "0x12", marketingName: "iPad Air (Cellular)", socName: "Apple A7", boardConfig: "j72ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,3", cpid: "0x8960", bdid: "0x14", marketingName: "iPad Air (TD-LTE)", socName: "Apple A7", boardConfig: "j73ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,7", cpid: "0x8960", bdid: "0x32", marketingName: "iPad mini 3 (Wi-Fi)", socName: "Apple A7", boardConfig: "j85ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,8", cpid: "0x8960", bdid: "0x34", marketingName: "iPad mini 3 (Cellular)", socName: "Apple A7", boardConfig: "j86ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,8_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,9", cpid: "0x8960", bdid: "0x36", marketingName: "iPad mini 3 (China)", socName: "Apple A7", boardConfig: "j87ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,9_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,4", cpid: "0x8960", bdid: "0x0A", marketingName: "iPad mini 2 (Wi-Fi)", socName: "Apple A7", boardConfig: "j85ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,5", cpid: "0x8960", bdid: "0x0C", marketingName: "iPad mini 2 (Cellular)", socName: "Apple A7", boardConfig: "j86ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,5_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad4,6", cpid: "0x8960", bdid: "0x0E", marketingName: "iPad mini 2 (China)", socName: "Apple A7", boardConfig: "j87ap", category: .ipad, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPad4,6_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad3,4", cpid: "0x8955", bdid: "0x00", marketingName: "iPad (4th gen, Wi-Fi)", socName: "Apple A6X", boardConfig: "p101ap", category: .ipad, latestSignedVersion: "10.3.3", defaultIpswPattern: "iPad3,4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad3,5", cpid: "0x8955", bdid: "0x02", marketingName: "iPad (4th gen, Cellular)", socName: "Apple A6X", boardConfig: "p102ap", category: .ipad, latestSignedVersion: "10.3.4", defaultIpswPattern: "iPad3,5_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad3,6", cpid: "0x8955", bdid: "0x04", marketingName: "iPad (4th gen, CDMA)", socName: "Apple A6X", boardConfig: "p103ap", category: .ipad, latestSignedVersion: "10.3.4", defaultIpswPattern: "iPad3,6_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad3,1", cpid: "0x8945", bdid: "0x00", marketingName: "iPad (3rd gen, Wi-Fi)", socName: "Apple A5X", boardConfig: "j1ap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad3,1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad3,2", cpid: "0x8945", bdid: "0x02", marketingName: "iPad (3rd gen, Cellular)", socName: "Apple A5X", boardConfig: "j2ap", category: .ipad, latestSignedVersion: "9.3.6", defaultIpswPattern: "iPad3,2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad3,3", cpid: "0x8945", bdid: "0x04", marketingName: "iPad (3rd gen, CDMA)", socName: "Apple A5X", boardConfig: "j2aap", category: .ipad, latestSignedVersion: "9.3.6", defaultIpswPattern: "iPad3,3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad2,5", cpid: "0x8942", bdid: "0x0A", marketingName: "iPad mini 1st (Wi-Fi)", socName: "Apple A5 Rev A", boardConfig: "p105ap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad2,5_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad2,6", cpid: "0x8942", bdid: "0x0C", marketingName: "iPad mini 1st (GSM)", socName: "Apple A5 Rev A", boardConfig: "p106ap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad2,6_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad2,7", cpid: "0x8942", bdid: "0x0E", marketingName: "iPad mini 1st (CDMA)", socName: "Apple A5 Rev A", boardConfig: "p107ap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad2,7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad2,1", cpid: "0x8940", bdid: "0x04", marketingName: "iPad 2 (Wi-Fi)", socName: "Apple A5", boardConfig: "k93ap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad2,1_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad2,2", cpid: "0x8940", bdid: "0x06", marketingName: "iPad 2 (GSM)", socName: "Apple A5", boardConfig: "k94ap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad2,2_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad2,3", cpid: "0x8940", bdid: "0x02", marketingName: "iPad 2 (CDMA)", socName: "Apple A5", boardConfig: "k95ap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad2,3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad2,4", cpid: "0x8942", bdid: "0x00", marketingName: "iPad 2 (Wi-Fi Mid 2012)", socName: "Apple A5 Rev A", boardConfig: "k93aap", category: .ipad, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPad2,4_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad1,1", cpid: "0x8930", bdid: "0x02", marketingName: "iPad (1st gen)", socName: "Apple A4", boardConfig: "k48ap", category: .ipad, latestSignedVersion: "5.1.1", defaultIpswPattern: "iPad1,1_5.1.1_Restore.ipsw"),

        // MARK: iPad Air (M3) & iPad (A16)
        AppleDeviceProfile(identifier: "iPad15,3", cpid: "0x8132", bdid: "0x10", marketingName: "iPad Air 11-inch (M3, Wi-Fi)", socName: "Apple M3", boardConfig: "j607ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_11.0_M3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad15,4", cpid: "0x8132", bdid: "0x12", marketingName: "iPad Air 11-inch (M3, Cellular)", socName: "Apple M3", boardConfig: "j608ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_11.0_M3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad15,5", cpid: "0x8132", bdid: "0x14", marketingName: "iPad Air 13-inch (M3, Wi-Fi)", socName: "Apple M3", boardConfig: "j637ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_13.0_M3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad15,6", cpid: "0x8132", bdid: "0x16", marketingName: "iPad Air 13-inch (M3, Cellular)", socName: "Apple M3", boardConfig: "j638ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_13.0_M3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad15,7", cpid: "0x8120", bdid: "0x10", marketingName: "iPad (A16, Wi-Fi)", socName: "Apple A16", boardConfig: "j481ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_A16_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPad15,8", cpid: "0x8120", bdid: "0x12", marketingName: "iPad (A16, Cellular)", socName: "Apple A16", boardConfig: "j482ap", category: .ipad, latestSignedVersion: "18.3.1", defaultIpswPattern: "iPad_A16_Restore.ipsw"),

        // MARK: iPod touch (5th, 6th, 7th gen)
        AppleDeviceProfile(identifier: "iPod9,1", cpid: "0x8010", bdid: "0x16", marketingName: "iPod touch (7th generation)", socName: "Apple A10 Fusion", boardConfig: "n112ap", category: .ipod, latestSignedVersion: "15.8.3", defaultIpswPattern: "iPodtouch_7_15.8.3_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPod7,1", cpid: "0x7000", bdid: "0x10", marketingName: "iPod touch (6th generation)", socName: "Apple A8", boardConfig: "n102ap", category: .ipod, latestSignedVersion: "12.5.7", defaultIpswPattern: "iPodtouch_6_12.5.7_Restore.ipsw"),
        AppleDeviceProfile(identifier: "iPod5,1", cpid: "0x8942", bdid: "0x00", marketingName: "iPod touch (5th generation)", socName: "Apple A5", boardConfig: "n78ap", category: .ipod, latestSignedVersion: "9.3.5", defaultIpswPattern: "iPodtouch_5_9.3.5_Restore.ipsw")
    ]

    // Fast lookup dictionaries
    private static let byIdentifier: [String: AppleDeviceProfile] = Dictionary(allDevices.map { ($0.identifier.uppercased(), $0) }, uniquingKeysWith: { first, _ in first })
    private static let byCpidBdid: [String: [AppleDeviceProfile]] = {
        var map: [String: [AppleDeviceProfile]] = [:]
        for d in allDevices {
            let key = "\(cleanHex(d.cpid)):\(cleanHex(d.bdid))"
            map[key, default: []].append(d)
        }
        return map
    }()

    private static func cleanHex(_ val: String) -> String {
        val.lowercased().replacingOccurrences(of: "0x", with: "")
    }

    public static func resolve(productType: String) -> AppleDeviceProfile? {
        byIdentifier[productType.trimmingCharacters(in: .whitespaces).uppercased()]
    }

    public static func resolveAll(cpid: String, bdid: String) -> [AppleDeviceProfile] {
        let key = "\(cleanHex(cpid)):\(cleanHex(bdid))"
        if let matches = byCpidBdid[key], !matches.isEmpty { return matches }
        return allDevices.filter { cleanHex($0.cpid) == cleanHex(cpid) }
    }

    public static func resolve(cpid: String, bdid: String) -> AppleDeviceProfile? {
        resolveAll(cpid: cpid, bdid: bdid).first
    }

    public static func resolveAllFromUsbSerial(_ rawSerial: String) -> [AppleDeviceProfile] {
        let upper = rawSerial.uppercased()
        var cpid = ""
        var bdid = ""

        if let cRange = upper.range(of: "CPID:") {
            let sub = upper[cRange.upperBound...]
            cpid = String(sub.prefix(4))
        }
        if let bRange = upper.range(of: "BDID:") {
            let sub = upper[bRange.upperBound...]
            bdid = String(sub.prefix(2))
        }

        if !cpid.isEmpty && !bdid.isEmpty {
            return resolveAll(cpid: "0x\(cpid)", bdid: "0x\(bdid)")
        } else if !cpid.isEmpty {
            return resolveAll(cpid: "0x\(cpid)", bdid: "")
        }
        return []
    }

    public static func resolveFromUsbSerial(_ rawSerial: String) -> AppleDeviceProfile? {
        resolveAllFromUsbSerial(rawSerial).first
    }
}

// MARK: - Multi-Brand Android OEM & Silicon Specification Matrix

public enum AndroidBrand: String, Codable, CaseIterable {
    case googlePixel = "Google Pixel"
    case samsung = "Samsung Galaxy"
    case xiaomi = "Xiaomi / Redmi / POCO"
    case motorola = "Motorola"
    case oneplus = "OnePlus"
    case oppo = "OPPO"
    case realme = "Realme"
    case vivo = "Vivo / iQOO"
    case sony = "Sony Xperia"
    case lg = "LG Electronics"
    case asus = "ASUS ROG / Zenfone"
    case huawei = "Huawei / Honor"
    case transsion = "Transsion (Tecno / Infinix / Itel)"
    case lenovo = "Lenovo"
    case zte = "ZTE / Nubia / RedMagic"
    case nothing = "Nothing Phone"
    case tclRevvl = "T-Mobile REVVL / TCL"
    case qualcommSilicon = "Qualcomm Snapdragon (Bare-Metal EDL)"
    case mediatekSilicon = "MediaTek Dimensity / Helio (Bare-Metal BROM)"
    case unisocSilicon = "Unisoc / Spreadtrum (Bare-Metal Diag)"
    case genericAndroid = "Generic AOSP Android"
}

public struct AndroidBrandProfile: Identifiable, Codable {
    public var id: String { brand.rawValue }
    public let brand: AndroidBrand
    public let vendorId: Int
    public let primaryAdbPids: [Int]
    public let primaryFastbootPids: [Int]
    public let hardwareTestCode: String
    public let engineeringMenuCode: String
    public let fastbootdSupported: Bool
    public let stockRomFormat: String
    public let chipFamilyHint: String
    public let controlCapabilities: [String]

    public var hardwareBootGuide: String {
        switch brand {
        case .tclRevvl:
            return "Power Off -> Hold Vol Up + Power for Recovery/Fastboot, OR Hold Vol Up + Vol Down while plugging USB for MTK BROM."
        case .samsung:
            return "Power Off -> Hold Vol Up + Vol Down while plugging USB for Odin Download Mode."
        case .googlePixel, .nothing, .sony:
            return "Power Off -> Hold Vol Down + Power for Bootloader / Fastboot."
        case .xiaomi:
            return "Power Off -> Hold Vol Down + Power for Fastboot, or Vol Up + Power for Mi Recovery."
        case .motorola, .lenovo:
            return "Power Off -> Hold Vol Down + Power for Bootloader / Fastboot."
        case .oneplus, .oppo, .realme:
            return "Power Off -> Hold Vol Up + Vol Down + Power for Fastboot, or Vol Up + Vol Down while plugging USB for EDL/BROM."
        case .vivo:
            return "Power Off -> Hold Vol Up + Power for Fastboot / Recovery."
        case .mediatekSilicon:
            return "MTK BROM Active -> Ready for 0xA00A5005 Handshake & Scatter Inspection."
        case .qualcommSilicon:
            return "Qualcomm EDL 9008 Active -> Ready for Sahara HELLO & Firehose Probe."
        case .unisocSilicon:
            return "Unisoc SCI Diag Active -> Ready for HDLC Ping & PAC Inspection."
        default:
            return "Enable USB Debugging in Developer Options, or hold Vol Down + Power from off state for Bootloader."
        }
    }
}

public struct AndroidBrandMasterRegistry {
    public static let allBrands: [AndroidBrandProfile] = [
        AndroidBrandProfile(
            brand: .googlePixel,
            vendorId: 0x18d1,
            primaryAdbPids: [0x4ee7, 0x4ee2],
            primaryFastbootPids: [0x4ee0],
            hardwareTestCode: "*#*#72786#*#* (SCRTN / Carrier Reset)",
            engineeringMenuCode: "*#*#4636#*#* (Testing Menu)",
            fastbootdSupported: true,
            stockRomFormat: "Factory Image .zip (flash-all.sh / boot.img / vendor_boot.img)",
            chipFamilyHint: "Google Tensor (G1-G4) / Qualcomm Snapdragon",
            controlCapabilities: ["Fastbootd Slot A/B Switch", "Logical Partition Resizing", "Recovery OTA Sideload", "Lock/Unlock State Query"]
        ),
        AndroidBrandProfile(
            brand: .samsung,
            vendorId: 0x04e8,
            primaryAdbPids: [0x6860],
            primaryFastbootPids: [0x685d], // Odin / Loke Download Mode
            hardwareTestCode: "*#0*# (General Hardware Diagnostic Test)",
            engineeringMenuCode: "*#*#4636#*#* / *#9900# (SysDump)",
            fastbootdSupported: false, // Uses Odin protocol
            stockRomFormat: "Tar.MD5 (BL, AP, CP, CSC, HOME_CSC)",
            chipFamilyHint: "Exynos / Qualcomm Snapdragon / MediaTek Dimensity",
            controlCapabilities: ["1-Click Exit Download Mode", "AT+DEVCONINFO Diagnostic Query", "FUS Cloud Odin Flasher", "EFS Radio Calibration Snapshot"]
        ),
        AndroidBrandProfile(
            brand: .xiaomi,
            vendorId: 0x2717,
            primaryAdbPids: [0xff08, 0xff18],
            primaryFastbootPids: [0xff40, 0xff48],
            hardwareTestCode: "*#*#6484#*#* (CIT Hardware Diagnostic Test)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "Fastboot TGZ (flash_all.sh / images/)",
            chipFamilyHint: "Qualcomm Snapdragon / MediaTek Dimensity",
            controlCapabilities: ["CIT Secret Menu Bridge", "Fastboot Slot Control", "Mi Assistant Recovery Reboot", "EDL 9008 Transition"]
        ),
        AndroidBrandProfile(
            brand: .motorola,
            vendorId: 0x22b8,
            primaryAdbPids: [0x2e76, 0x2e81],
            primaryFastbootPids: [0x2e80],
            hardwareTestCode: "*#*#2486#*#* (CQA Factory Test Menu)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "flashfile.xml (fastboot XML script)",
            chipFamilyHint: "Qualcomm Snapdragon / MediaTek Helio",
            controlCapabilities: ["Read get_unlock_data (Bootloader Token)", "CQA Menu Bridge", "Fastbootd Logical Partitions", "Blankflash Recovery"]
        ),
        AndroidBrandProfile(
            brand: .oneplus,
            vendorId: 0x2a70,
            primaryAdbPids: [0x9011, 0x4ee7],
            primaryFastbootPids: [0xf003],
            hardwareTestCode: "*#899# (Engineer Mode Aftersales Test)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "payload.bin / .ofp container",
            chipFamilyHint: "Qualcomm Snapdragon / MediaTek Dimensity",
            controlCapabilities: ["payload.bin 1-Click Extraction", "Fastboot Slot Switch", "Engineer Mode Launcher", "Qualcomm EDL 9008 Sahara"]
        ),
        AndroidBrandProfile(
            brand: .oppo,
            vendorId: 0x22d9,
            primaryAdbPids: [0x2769],
            primaryFastbootPids: [0x0001],
            hardwareTestCode: "*#899# (Manual Hardware Test)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: ".ofp / .ozip container",
            chipFamilyHint: "Qualcomm Snapdragon / MediaTek Dimensity",
            controlCapabilities: ["Engineer Test Menu", "Fastboot Dynamic Partitions", "ADB Sideload"]
        ),
        AndroidBrandProfile(
            brand: .vivo,
            vendorId: 0x2b4c,
            primaryAdbPids: [0x0001],
            primaryFastbootPids: [0x0002],
            hardwareTestCode: "*#558# (Factory Test Engineering Menu)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "OTA package / payload.bin",
            chipFamilyHint: "MediaTek Dimensity / Qualcomm Snapdragon",
            controlCapabilities: ["Fastboot Slot Control", "Factory Test Dispatcher", "ADB Package Manager"]
        ),
        AndroidBrandProfile(
            brand: .sony,
            vendorId: 0x0fce,
            primaryAdbPids: [0x61da],
            primaryFastbootPids: [0x0dde], // Blue LED Fastboot (0xadde = Flashmode Green LED)
            hardwareTestCode: "*#*#7378423#*#* (*#*#SERVICE#*#*)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "Xperia Sin / Newflasher bundle",
            chipFamilyHint: "Qualcomm Snapdragon",
            controlCapabilities: ["Xperia Service Menu Launcher", "Fastboot Mode Controller", "Flashmode Detection"]
        ),
        AndroidBrandProfile(
            brand: .lg,
            vendorId: 0x1004,
            primaryAdbPids: [0x633e],
            primaryFastbootPids: [0x633e], // LAF Download Mode
            hardwareTestCode: "*#546368#*<model># (LG Hidden Menu)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "KDZ / DZ container",
            chipFamilyHint: "Qualcomm Snapdragon / MediaTek",
            controlCapabilities: ["Hidden Menu Dispatcher", "LAF Download Mode Detection", "Fastboot Flasher"]
        ),
        AndroidBrandProfile(
            brand: .asus,
            vendorId: 0x0b05,
            primaryAdbPids: [0x7770],
            primaryFastbootPids: [0x7772],
            hardwareTestCode: ".12345+= (Calculator Hardware SMMI Test)",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "raw firmware ZIP",
            chipFamilyHint: "Qualcomm Snapdragon (ROG Phone / Zenfone)",
            controlCapabilities: ["Fastbootd Slot A/B Control", "Raw Firmware Ingestion", "ADB Recovery Sideload"]
        ),
        AndroidBrandProfile(
            brand: .transsion,
            vendorId: 0x3317,
            primaryAdbPids: [0x0001],
            primaryFastbootPids: [0x0002],
            hardwareTestCode: "*#*#83781#*#* / *#*#4636#*#*",
            engineeringMenuCode: "*#*#83781#*#*",
            fastbootdSupported: true,
            stockRomFormat: "Scatter.txt / PAC archive",
            chipFamilyHint: "MediaTek Helio / Unisoc Tiger",
            controlCapabilities: ["MTK BROM / Preloader Handshake", "Unisoc SCI Diag Interrogation", "Fastboot Partition Flasher"]
        ),
        AndroidBrandProfile(
            brand: .nothing,
            vendorId: 0x2970,
            primaryAdbPids: [0x4ee7],
            primaryFastbootPids: [0xf003],
            hardwareTestCode: "*#*#4636#*#*",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "payload.bin OTA",
            chipFamilyHint: "Qualcomm Snapdragon / MediaTek Dimensity",
            controlCapabilities: ["payload.bin Dumper", "Fastbootd Slot A/B", "Glyph LED Hardware Diagnostics"]
        ),
        AndroidBrandProfile(
            brand: .huawei,
            vendorId: 0x12d1,
            primaryAdbPids: [0x1037, 0x1052],
            primaryFastbootPids: [0x107e],
            hardwareTestCode: "*#*#2846579#*#* (ProjectMenu)",
            engineeringMenuCode: "*#*#2846579#*#*",
            fastbootdSupported: true,
            stockRomFormat: "UPDATE.APP archive",
            chipFamilyHint: "HiSilicon Kirin / Qualcomm Snapdragon",
            controlCapabilities: ["ProjectMenu Diag Launcher", "Fastboot Partition Audit", "eRecovery Kick"]
        ),
        AndroidBrandProfile(
            brand: .lenovo,
            vendorId: 0x17ef,
            primaryAdbPids: [0x7900, 0x7901],
            primaryFastbootPids: [0x7904],
            hardwareTestCode: "####1111# (Factory Test Menu)",
            engineeringMenuCode: "####1111#",
            fastbootdSupported: true,
            stockRomFormat: "QFIL / Scatter / PAC archive",
            chipFamilyHint: "Qualcomm Snapdragon / MediaTek Dimensity",
            controlCapabilities: ["Lenovo Service Mode Launcher", "Fastbootd Slot A/B", "EDL Kick"]
        ),
        AndroidBrandProfile(
            brand: .zte,
            vendorId: 0x19d2,
            primaryAdbPids: [0x0112, 0x0113],
            primaryFastbootPids: [0x0016],
            hardwareTestCode: "*983*0# / *983*70#",
            engineeringMenuCode: "*983*0#",
            fastbootdSupported: true,
            stockRomFormat: "update.zip / Firehose rawprogram",
            chipFamilyHint: "Qualcomm Snapdragon (RedMagic / Nubia)",
            controlCapabilities: ["ZTE Test Interface", "Fastboot Partition Flasher", "Sahara EDL Probe"]
        ),
        AndroidBrandProfile(
            brand: .tclRevvl,
            vendorId: 0x1bbb,
            primaryAdbPids: [0x0168, 0x0169],
            primaryFastbootPids: [0x0170],
            hardwareTestCode: "*#*#4636#*#* / ###2324#",
            engineeringMenuCode: "*#*#4636#*#*",
            fastbootdSupported: true,
            stockRomFormat: "Scatter.txt / Fastboot super.img",
            chipFamilyHint: "MediaTek Helio / Dimensity MT8768",
            controlCapabilities: ["Fastbootd Dynamic Partitions", "MTK BROM Handshake", "1-Click Mode Rebooter"]
        ),
        // Bare-Metal Silicon Interfaces
        AndroidBrandProfile(
            brand: .qualcommSilicon,
            vendorId: 0x05c6,
            primaryAdbPids: [],
            primaryFastbootPids: [0x9008], // EDL Mode
            hardwareTestCode: "Sahara Command 0x01 (HELLO Handshake)",
            engineeringMenuCode: "Firehose XML Programmer Protocol",
            fastbootdSupported: false,
            stockRomFormat: "rawprogram0.xml + patch0.xml + prog_firehose_*.elf",
            chipFamilyHint: "Qualcomm Snapdragon BootROM",
            controlCapabilities: ["Sahara HELLO Probe", "Serial / HW_ID Extraction", "1-Click EDL Reboot / Reset"]
        ),
        AndroidBrandProfile(
            brand: .mediatekSilicon,
            vendorId: 0x0e8d,
            primaryAdbPids: [],
            primaryFastbootPids: [0x0003, 0x2000], // BROM / Preloader
            hardwareTestCode: "0xA00A5005 MTK Handshake Sequence",
            engineeringMenuCode: "Download Agent (DA) Protocol",
            fastbootdSupported: false,
            stockRomFormat: "scatter.txt + partition binaries",
            chipFamilyHint: "MediaTek Helio / Dimensity BootROM",
            controlCapabilities: ["BROM 0e8d:0003 Handshake", "Hardware Chip Code Query", "Preloader VCOM Probe"]
        ),
        AndroidBrandProfile(
            brand: .unisocSilicon,
            vendorId: 0x1782,
            primaryAdbPids: [],
            primaryFastbootPids: [0x4d00], // SCI USB Diag Port
            hardwareTestCode: "HDLC Framing 0x7E Ping",
            engineeringMenuCode: "FDL1 / FDL2 Protocol",
            fastbootdSupported: false,
            stockRomFormat: ".PAC firmware container",
            chipFamilyHint: "Unisoc / Spreadtrum BootROM",
            controlCapabilities: ["SCI Diag Handshake", "FDL Stage Interrogation", "PAC Archive Parser"]
        )
    ]

    private static let byVendorId: [Int: AndroidBrandProfile] = Dictionary(allBrands.map { ($0.vendorId, $0) }, uniquingKeysWith: { first, _ in first })

    public static func resolve(vendorId: Int) -> AndroidBrandProfile? {
        byVendorId[vendorId]
    }

    public static func resolve(model: String) -> AndroidBrandProfile? {
        let lower = model.lowercased()
        if lower.contains("pixel") { return byVendorId[0x18d1] }
        if lower.contains("sm-") || lower.contains("samsung") || lower.contains("galaxy") { return byVendorId[0x04e8] }
        if lower.contains("redmi") || lower.contains("xiaomi") || lower.contains("poco") { return byVendorId[0x2717] }
        if lower.contains("moto") || lower.contains("motorola") { return byVendorId[0x22b8] }
        if lower.contains("oneplus") { return byVendorId[0x2a70] }
        if lower.contains("oppo") { return byVendorId[0x22d9] }
        if lower.contains("vivo") || lower.contains("iqoo") { return byVendorId[0x2b4c] }
        if lower.contains("xperia") || lower.contains("sony") { return byVendorId[0x0fce] }
        if lower.contains("lg") { return byVendorId[0x1004] }
        if lower.contains("asus") || lower.contains("rog") { return byVendorId[0x0b05] }
        if lower.contains("tecno") || lower.contains("infinix") || lower.contains("itel") { return byVendorId[0x3317] }
        if lower.contains("nothing") { return byVendorId[0x2970] }
        if lower.contains("huawei") || lower.contains("honor") { return byVendorId[0x12d1] }
        if lower.contains("lenovo") { return byVendorId[0x17ef] }
        if lower.contains("zte") || lower.contains("nubia") || lower.contains("redmagic") { return byVendorId[0x19d2] }
        if lower.contains("revvl") || lower.contains("tcl") || lower.contains("alcatel") { return byVendorId[0x1bbb] }
        return nil
    }
}
