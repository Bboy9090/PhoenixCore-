import {
  ScrollView,
  View,
  Text,
  Pressable,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Animated,
  Image,
} from 'react-native';
import { useState, useEffect, useRef } from 'react';
import QRCode from 'qrcode';
import {
  scanUSBDevicesAsync,
  detectDevice,
  BUILD_STAGES,
  runBuild,
  validateRecipe,
  runSafetyCheck,
  type PhoenixUSBDevice,
  type PhoenixRecipe,
  type ValidationResult,
  type SafetyCheckResult,
  type BuildProgress,
  type SelectedOSItem,
  type SelectedToolItem,
} from '@/lib/phoenix-engine';
import { OS_CATALOG, TOOL_CATALOG } from '@/lib/data/catalog';
import { useColors } from '@/hooks/use-colors';
import { ScreenContainer } from '@/components/screen-container';

// ─── Procedural Audio Synthesizer ─────────────────────────────────────────────

class PhoenixAudio {
  private static ctx: AudioContext | null = null;
  
  private static init() {
    if (typeof window === 'undefined') return;
    if (!this.ctx) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioContextClass) {
        this.ctx = new AudioContextClass();
      }
    }
  }

  public static playClick() {
    try {
      this.init();
      if (!this.ctx) return;
      
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1200, this.ctx.currentTime + 0.04);
      
      gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.04);
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start();
      osc.stop(this.ctx.currentTime + 0.05);
    } catch {
      // Ignore audio context blockages
    }
  }

  public static playChime() {
    try {
      this.init();
      if (!this.ctx) return;
      
      const now = this.ctx.currentTime;
      const freqs = [523.25, 659.25, 783.99, 1046.50]; // C5 -> E5 -> G5 -> C6 arpeggio
      
      freqs.forEach((freq, i) => {
        const osc = this.ctx!.createOscillator();
        const gain = this.ctx!.createGain();
        
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(freq, now + i * 0.07);
        
        gain.gain.setValueAtTime(0.0, now + i * 0.07);
        gain.gain.linearRampToValueAtTime(0.05, now + i * 0.07 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + i * 0.07 + 0.25);
        
        osc.connect(gain);
        gain.connect(this.ctx!.destination);
        
        osc.start(now + i * 0.07);
        osc.stop(now + i * 0.07 + 0.3);
      });
    } catch {
      // Ignore
    }
  }

  public static playTick() {
    try {
      this.init();
      if (!this.ctx) return;
      
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(160, this.ctx.currentTime);
      
      gain.gain.setValueAtTime(0.03, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.02);
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      
      osc.start();
      osc.stop(this.ctx.currentTime + 0.03);
    } catch {
      // Ignore
    }
  }
}

// ─── Constants ────────────────────────────────────────────────────────────────

const BG = '#050811';
const CARD = '#0a0e1a';
const BLUE = '#00d2ff';
const GOLD = '#ffd700';
const PURPLE = '#9d4edd';
const CYAN = '#00ffff';
const MUTED = '#94a3b8';
const BORDER = '#1a2035';

const STEP_LABELS = ['OS', 'Tools', 'Device', 'Recipe', 'Validate', 'Safety', 'Build', 'Done'];

const PHOENIX_OS_SUITE: SelectedOSItem[] = [
  { id: 'home-aurelia', name: 'Home Aurelia', version: '3.2', sizeGB: 4.5, color: GOLD, category: 'linux' },
  { id: 'blue-phoenix', name: 'Blue Phoenix OS', version: '2.1', sizeGB: 6.2, color: BLUE, category: 'linux' },
  { id: 'arcwyre', name: 'Arcwyre', version: '1.5', sizeGB: 5.8, color: PURPLE, category: 'linux' },
  { id: 'thunder-god', name: 'Thunder God', version: '1.0', sizeGB: 7.1, color: CYAN, category: 'linux' },
];

// ─── Helper functions ─────────────────────────────────────────────────────────

function formatSize(sizeGB: number): string {
  if (sizeGB >= 1) return sizeGB.toFixed(1) + ' GB';
  return Math.round(sizeGB * 1024) + ' MB';
}

function healthColor(health: string): string {
  if (health === 'healthy') return '#22c55e';
  if (health === 'warning') return GOLD;
  return '#ef4444';
}

function riskColor(risk: string): string {
  if (risk === 'low') return '#22c55e';
  if (risk === 'medium') return GOLD;
  return '#ef4444';
}

function etaString(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m === 0) return s + ' sec remaining';
  return m + ' min ' + s + ' sec remaining';
}

// ─── Step Indicator ───────────────────────────────────────────────────────────

function StepIndicator({ currentStep }: { currentStep: number }) {
  return (
    <View style={styles.stepRow}>
      {STEP_LABELS.map((label, i) => {
        const stepNum = i + 1;
        const isActive = stepNum === currentStep;
        const isPast = stepNum < currentStep;
        const dotColor = isActive ? BLUE : isPast ? BLUE + '80' : MUTED + '40';
        const labelColor = isActive ? BLUE : isPast ? MUTED : MUTED + '60';
        return (
          <View key={label} style={styles.stepItem}>
            {i > 0 && (
              <View style={[styles.stepLine, { backgroundColor: isPast || isActive ? BLUE + '60' : MUTED + '20' }]} />
            )}
            <View style={[styles.stepDot, { backgroundColor: dotColor, borderColor: isActive ? BLUE : 'transparent', borderWidth: isActive ? 2 : 0 }]} />
            <Text style={[styles.stepLabel, { color: labelColor }]}>{label}</Text>
          </View>
        );
      })}
    </View>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function BuilderScreen() {
  const colors = useColors();

  // Step state
  const [step, setStep] = useState(1);

  // Step 1 — OS selection
  const [selectedOS, setSelectedOS] = useState<SelectedOSItem[]>([]);
  const [customOSList, setCustomOSList] = useState<SelectedOSItem[]>([]);
  const [customName, setCustomName] = useState('');
  const [customSize, setCustomSize] = useState('5.0');
  const [customCategory, setCustomCategory] = useState('linux');

  // Step 2 — Tool selection
  const [selectedTools, setSelectedTools] = useState<SelectedToolItem[]>([]);

  // Step 3 — USB devices
  const [usbDevices, setUsbDevices] = useState<PhoenixUSBDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<PhoenixUSBDevice | null>(null);
  const [scanning, setScanning] = useState(false);

  // Step 4 — Recipe
  const [recipe, setRecipe] = useState<PhoenixRecipe | null>(null);
  const [qrUri, setQrUri] = useState<string | null>(null);

  // Step 5 — Validation
  const [validation, setValidation] = useState<ValidationResult | null>(null);

  // Step 6 — Safety
  const [safety, setSafety] = useState<SafetyCheckResult | null>(null);
  const [confirmInput, setConfirmInput] = useState('');

  // Step 7 — Build
  const [buildProgress, setBuildProgress] = useState<BuildProgress | null>(null);
  const [completedStages, setCompletedStages] = useState<Set<string>>(new Set());
  const progressAnim = useRef(new Animated.Value(0)).current;
  const cancelBuildRef = useRef<(() => void) | null>(null);

  // Step 8 — Complete
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const [buildStartRef, setBuildStartRef] = useState<number>(0);
  const [buildEndTime, setBuildEndTime] = useState<number>(0);

  // ── Step 1: OS selection logic ──

  function isOSSelected(id: string) {
    return selectedOS.some(o => o.id === id);
  }

  function togglePhoenixOS(item: SelectedOSItem) {
    PhoenixAudio.playClick();
    setSelectedOS(prev => {
      const exists = prev.some(o => o.id === item.id);
      return exists ? prev.filter(o => o.id !== item.id) : [...prev, item];
    });
  }

  function toggleCatalogOS(item: typeof OS_CATALOG[0]) {
    PhoenixAudio.playClick();
    const mapped: SelectedOSItem = {
      id: item.id,
      name: item.name,
      version: item.version,
      sizeGB: item.sizeGB,
      color: item.color,
      category: item.category,
    };
    setSelectedOS(prev => {
      const exists = prev.some(o => o.id === item.id);
      return exists ? prev.filter(o => o.id !== item.id) : [...prev, mapped];
    });
  }

  function handleAddCustomOS() {
    if (!customName.trim()) return;
    const size = parseFloat(customSize) || 4.5;
    const newItem: SelectedOSItem = {
      id: `custom-${Date.now()}`,
      name: customName.trim(),
      version: '1.0',
      sizeGB: size,
      color: PURPLE,
      category: customCategory,
    };
    
    setCustomOSList(prev => [...prev, newItem]);
    setSelectedOS(prev => [...prev, newItem]);
    setCustomName('');
    PhoenixAudio.playChime();
  }

  // ── Step 2: Tool selection logic ──

  function isToolSelected(id: string) {
    return selectedTools.some(t => t.id === id);
  }

  function toggleTool(item: typeof TOOL_CATALOG[0]) {
    PhoenixAudio.playClick();
    const mapped: SelectedToolItem = {
      id: item.id,
      name: item.name,
      sizeGB: item.sizeGB,
      color: item.color,
      category: item.category,
    };
    setSelectedTools(prev => {
      const exists = prev.some(t => t.id === item.id);
      return exists ? prev.filter(t => t.id !== item.id) : [...prev, mapped];
    });
  }

  // ── Step 3: USB scanning ──

  async function triggerUSBScan() {
    PhoenixAudio.playClick();
    setScanning(true);
    try {
      const list = await scanUSBDevicesAsync();
      setUsbDevices(list);
    } finally {
      setScanning(false);
    }
  }

  useEffect(() => {
    if (step === 3) {
      triggerUSBScan();
    }
  }, [step]);

  // ── Step 4: Recipe building & QR Generation ──

  useEffect(() => {
    if (step === 4) {
      const devProfile = detectDevice();
      const totalSizeGB = selectedOS.reduce((s, o) => s + o.sizeGB, 0) +
        selectedTools.reduce((s, t) => s + t.sizeGB, 0);

      const estimatedMinutes = Math.max(3, Math.ceil(totalSizeGB * 0.5));
      const isMac = devProfile.platform === 'macos' || (devProfile.platform === 'web' && typeof navigator !== 'undefined' && /Mac/.test(navigator.userAgent));
      
      const newRecipe: PhoenixRecipe = {
        id: `recipe-${Date.now()}`,
        name: `Phoenix USB — ${selectedOS.map(o => o.name).join(', ')}`,
        createdAt: new Date().toISOString(),
        deviceType: devProfile.deviceType,
        targetDevice: selectedDevice,
        selectedOS,
        selectedTools,
        totalSizeGB,
        estimatedMinutes,
        partitionScheme: 'gpt',
        bootloader: devProfile.deviceType === 'pc-laptop' ? 'hybrid' : 'uefi',
        safetyLevel: 'standard',
        ventoyMacMode: isMac,
        ventoyCommand: isMac ? `sudo sh Ventoy2Disk.sh -i ${selectedDevice?.path || '/dev/disk2'}` : `Ventoy2Disk.exe /I ${selectedDevice?.path || '/dev/disk2'}`,
        platform: isMac ? 'macos' : 'windows',
      };

      setRecipe(newRecipe);

      // Generate compact recipe payload for QR Code
      const compactRecipe = {
        id: newRecipe.id,
        os: newRecipe.selectedOS.map(o => ({ id: o.id, size: o.sizeGB })),
        tools: newRecipe.selectedTools.map(t => t.id),
        device: selectedDevice?.name || 'USB Disk'
      };

      QRCode.toDataURL(JSON.stringify(compactRecipe), {
        color: {
          dark: '#00d2ff',
          light: '#0a0e1a'
        },
        margin: 2,
        width: 200,
      })
      .then(url => setQrUri(url))
      .catch(err => console.error('QR Code generation failed:', err));
    }
  }, [step, selectedOS, selectedTools, selectedDevice]);

  function adjustOSSize(id: string, delta: number) {
    PhoenixAudio.playClick();
    setSelectedOS(prev =>
      prev.map(o => {
        if (o.id === id) {
          const newSize = Math.max(1.0, Math.min(50.0, o.sizeGB + delta));
          return { ...o, sizeGB: newSize };
        }
        return o;
      })
    );
  }

  // ── Step 5: Validation ──

  function handleValidate() {
    if (!recipe) return;
    PhoenixAudio.playClick();
    setValidation(validateRecipe(recipe));
    setStep(5);
  }

  // ── Step 6: Safety check ──

  function handleSafetyCheck() {
    if (!recipe) return;
    PhoenixAudio.playClick();
    setSafety(runSafetyCheck(recipe));
    setStep(6);
  }

  // ── Step 7: Build ──

  useEffect(() => {
    if (step === 7 && recipe) {
      setBuildStartRef(Date.now());
      setCompletedStages(new Set());
      setBuildProgress(null);

      let lastStage = '';

      const cancel = runBuild(
        recipe,
        (progress) => {
          setBuildProgress(progress);
          
          if (progress.stage !== lastStage && lastStage !== '') {
            PhoenixAudio.playTick();
            setCompletedStages(prev => new Set([...prev, lastStage]));
          }
          lastStage = progress.stage;

          Animated.timing(progressAnim, {
            toValue: progress.overallProgress / 100,
            duration: 250,
            useNativeDriver: false,
          }).start();
        },
        (success) => {
          setBuildEndTime(Date.now());
          if (success) {
            PhoenixAudio.playChime();
            const allStages = BUILD_STAGES.map(s => s.id);
            setCompletedStages(new Set(allStages));
            setTimeout(() => setStep(8), 650);
          }
        }
      );

      cancelBuildRef.current = cancel;
      return () => { cancel(); };
    }
  }, [step]);

  // ── Step 8: Pulse animation ──

  useEffect(() => {
    if (step === 8) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.12, duration: 650, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1.0, duration: 650, useNativeDriver: true }),
        ])
      ).start();
    }
  }, [step]);

  // ── Reset ──

  function resetAll() {
    PhoenixAudio.playClick();
    setStep(1);
    setSelectedOS([]);
    setCustomOSList([]);
    setSelectedTools([]);
    setSelectedDevice(null);
    setUsbDevices([]);
    setRecipe(null);
    setValidation(null);
    setSafety(null);
    setConfirmInput('');
    setBuildProgress(null);
    setCompletedStages(new Set());
    progressAnim.setValue(0);
    setBuildEndTime(0);
    setQrUri(null);
  }

  // ─── Render steps ─────────────────────────────────────────────────────────

  function renderStep1() {
    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionTitle}>⚡ Phoenix OS Suite</Text>
        {PHOENIX_OS_SUITE.map(item => {
          const selected = isOSSelected(item.id);
          return (
            <Pressable key={item.id} onPress={() => togglePhoenixOS(item)}
              style={[styles.card, { borderLeftColor: item.color, borderLeftWidth: 4, borderColor: selected ? item.color + '60' : BORDER, backgroundColor: selected ? item.color + '12' : CARD }]}>
              <View style={[styles.checkbox, { borderColor: selected ? item.color : MUTED, backgroundColor: selected ? item.color : 'transparent' }]}>
                {selected && <Text style={styles.checkMark}>✓</Text>}
              </View>
              <View style={styles.cardBody}>
                <Text style={[styles.cardTitle, { color: '#ffffff' }]}>{item.name}</Text>
                <View style={styles.badgeRow}>
                  <View style={[styles.badge, { backgroundColor: item.color + '22' }]}>
                    <Text style={[styles.badgeText, { color: item.color }]}>v{item.version}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: MUTED + '18' }]}>
                    <Text style={[styles.badgeText, { color: MUTED }]}>{formatSize(item.sizeGB)}</Text>
                  </View>
                </View>
              </View>
            </Pressable>
          );
        })}

        {customOSList.map(item => {
          const selected = isOSSelected(item.id);
          return (
            <Pressable key={item.id} onPress={() => togglePhoenixOS(item)}
              style={[styles.card, { borderLeftColor: item.color, borderLeftWidth: 4, borderColor: selected ? item.color + '60' : BORDER, backgroundColor: selected ? item.color + '12' : CARD }]}>
              <View style={[styles.checkbox, { borderColor: selected ? item.color : MUTED, backgroundColor: selected ? item.color : 'transparent' }]}>
                {selected && <Text style={styles.checkMark}>✓</Text>}
              </View>
              <View style={styles.cardBody}>
                <Text style={[styles.cardTitle, { color: '#ffffff' }]}>{item.name}</Text>
                <View style={styles.badgeRow}>
                  <View style={[styles.badge, { backgroundColor: item.color + '22' }]}>
                    <Text style={[styles.badgeText, { color: item.color }]}>v{item.version}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: MUTED + '18' }]}>
                    <Text style={[styles.badgeText, { color: MUTED }]}>{formatSize(item.sizeGB)}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: PURPLE + '18' }]}>
                    <Text style={[styles.badgeText, { color: PURPLE }]}>CUSTOM</Text>
                  </View>
                </View>
              </View>
            </Pressable>
          );
        })}

        <Text style={[styles.sectionTitle, { marginTop: 20 }]}>Operating Systems</Text>
        {OS_CATALOG.map(os => {
          const selected = isOSSelected(os.id);
          return (
            <Pressable key={os.id} onPress={() => toggleCatalogOS(os)}
              style={[styles.card, { borderLeftColor: os.color, borderLeftWidth: 4, borderColor: selected ? os.color + '60' : BORDER, backgroundColor: selected ? os.color + '12' : CARD }]}>
              <View style={[styles.checkbox, { borderColor: selected ? os.color : MUTED, backgroundColor: selected ? os.color : 'transparent' }]}>
                {selected && <Text style={styles.checkMark}>✓</Text>}
              </View>
              <View style={styles.cardBody}>
                <Text style={[styles.cardTitle, { color: '#ffffff' }]}>{os.name}</Text>
                <View style={styles.badgeRow}>
                  <View style={[styles.badge, { backgroundColor: os.color + '22' }]}>
                    <Text style={[styles.badgeText, { color: os.color }]}>v{os.version}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: MUTED + '18' }]}>
                    <Text style={[styles.badgeText, { color: MUTED }]}>{formatSize(os.sizeGB)}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: MUTED + '14' }]}>
                    <Text style={[styles.badgeText, { color: MUTED }]}>{os.category}</Text>
                  </View>
                </View>
              </View>
            </Pressable>
          );
        })}

        {/* Custom ISO Importer Panel */}
        <View style={[styles.card, styles.customImporterCard]}>
          <Text style={[styles.sectionTitle, { color: PURPLE, fontSize: 16 }]}>📁 Custom ISO Importer</Text>
          <Text style={[styles.cardDesc, { color: MUTED, marginBottom: 12 }]}>Import local operating system ISO recovery files securely.</Text>
          
          <TextInput
            placeholder="ISO Friendly Name (e.g., Windows Tiny11)"
            placeholderTextColor={MUTED + '80'}
            style={styles.customInput}
            value={customName}
            onChangeText={setCustomName}
          />
          
          <View style={styles.rowBetween}>
            <TextInput
              placeholder="Size in GB (e.g., 4.5)"
              placeholderTextColor={MUTED + '80'}
              keyboardType="decimal-pad"
              style={[styles.customInput, { flex: 1, marginRight: 8 }]}
              value={customSize}
              onChangeText={setCustomSize}
            />
            
            <View style={styles.customSelectBox}>
              <TouchableOpacity onPress={() => setCustomCategory(prev => prev === 'linux' ? 'windows' : 'linux')} style={styles.selectToggle}>
                <Text style={styles.selectToggleText}>{customCategory.toUpperCase()}</Text>
              </TouchableOpacity>
            </View>
          </View>

          <TouchableOpacity onPress={handleAddCustomOS} style={[styles.primaryBtn, { backgroundColor: PURPLE, height: 38, marginTop: 4 }]}>
            <Text style={styles.primaryBtnText}>➕ Add Custom ISO</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  }

  function renderStep2() {
    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <Text style={styles.sectionTitle}>🔧 Recovery & Diagnostic Tools</Text>
        {TOOL_CATALOG.map(tool => {
          const selected = isToolSelected(tool.id);
          return (
            <Pressable key={tool.id} onPress={() => toggleTool(tool)}
              style={[styles.card, { borderLeftColor: tool.color, borderLeftWidth: 4, borderColor: selected ? tool.color + '60' : BORDER, backgroundColor: selected ? tool.color + '12' : CARD }]}>
              <View style={[styles.checkbox, { borderColor: selected ? tool.color : MUTED, backgroundColor: selected ? tool.color : 'transparent' }]}>
                {selected && <Text style={styles.checkMark}>✓</Text>}
              </View>
              <View style={styles.cardBody}>
                <Text style={[styles.cardTitle, { color: '#ffffff' }]}>{tool.name}</Text>
                <View style={styles.badgeRow}>
                  <View style={[styles.badge, { backgroundColor: tool.color + '22' }]}>
                    <Text style={[styles.badgeText, { color: tool.color }]}>{tool.category}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: MUTED + '18' }]}>
                    <Text style={[styles.badgeText, { color: MUTED }]}>{formatSize(tool.sizeGB)}</Text>
                  </View>
                </View>
                <Text style={styles.cardDesc} numberOfLines={2}>{tool.description}</Text>
              </View>
            </Pressable>
          );
        })}
        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  }

  function renderStep3() {
    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.rowBetween}>
          <Text style={styles.sectionTitle}>💾 USB Devices</Text>
          <TouchableOpacity onPress={triggerUSBScan} style={styles.refreshBtn} disabled={scanning}>
            <Text style={[styles.refreshBtnText, { color: BLUE }]}>{scanning ? 'Scanning...' : '⟳ Refresh'}</Text>
          </TouchableOpacity>
        </View>

        {scanning && (
          <View style={styles.shimmerContainer}>
            <View style={styles.shimmerBar} />
            <View style={[styles.shimmerBar, { width: '80%', marginTop: 10 }]} />
            <View style={[styles.shimmerBar, { width: '50%', marginTop: 10 }]} />
          </View>
        )}

        {!scanning && usbDevices.length === 0 && (
          <View style={[styles.card, { alignItems: 'center', paddingVertical: 32 }]}>
            <Text style={{ fontSize: 40 }}>🔌</Text>
            <Text style={[styles.cardTitle, { color: MUTED, marginTop: 10 }]}>No USB devices found</Text>
            <Text style={[styles.cardDesc, { textAlign: 'center', marginTop: 4 }]}>Plug in a USB drive and tap Refresh</Text>
          </View>
        )}

        {!scanning && usbDevices.map(dev => {
          const selected = selectedDevice?.id === dev.id;
          const hc = healthColor(dev.healthStatus);
          return (
            <Pressable key={dev.id} onPress={() => { PhoenixAudio.playClick(); setSelectedDevice(dev); }}
              style={[styles.card, { borderColor: selected ? BLUE + '80' : BORDER, backgroundColor: selected ? BLUE + '10' : CARD }]}>
              <View style={[styles.radio, { borderColor: selected ? BLUE : MUTED }]}>
                {selected && <View style={styles.radioDot} />}
              </View>
              <View style={styles.cardBody}>
                <Text style={[styles.cardTitle, { color: '#ffffff' }]}>{dev.name}</Text>
                <View style={styles.badgeRow}>
                  <View style={[styles.badge, { backgroundColor: MUTED + '18' }]}>
                    <Text style={[styles.badgeText, { color: MUTED }]}>{dev.sizeFormatted}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: MUTED + '18' }]}>
                    <Text style={[styles.badgeText, { color: MUTED }]}>{dev.filesystem}</Text>
                  </View>
                  <View style={[styles.badge, { backgroundColor: hc + '22' }]}>
                    <Text style={[styles.badgeText, { color: hc }]}>{dev.healthStatus.toUpperCase()}</Text>
                  </View>
                </View>
                <Text style={[styles.cardDesc, { color: MUTED }]}>{dev.path} · {dev.writeSpeedMbps} MB/s write</Text>
              </View>
            </Pressable>
          );
        })}
        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  }

  function renderPartitionBar() {
    if (!recipe || !recipe.targetDevice) return null;
    const usbSize = recipe.targetDevice.sizeGB;
    const osSizes = recipe.selectedOS.reduce((acc, o) => acc + o.sizeGB, 0);
    const toolSizes = recipe.selectedTools.reduce((acc, t) => acc + t.sizeGB, 0);
    const totalSelected = osSizes + toolSizes;
    const freeSpace = Math.max(0, usbSize - totalSelected);
    
    return (
      <View style={[styles.card, { marginTop: 12 }]}>
        <Text style={[styles.sectionTitle, { marginBottom: 10, fontSize: 14 }]}>⚡ Dynamic USB Partition Map</Text>
        <View style={styles.partitionBarContainer}>
          {recipe.selectedOS.map(os => {
            const pct = (os.sizeGB / usbSize) * 100;
            if (pct <= 0) return null;
            return (
              <View key={os.id} style={[styles.partitionSegment, { width: `${pct}%`, backgroundColor: os.color }]} />
            );
          })}
          {recipe.selectedTools.map(tool => {
            const pct = (tool.sizeGB / usbSize) * 100;
            if (pct <= 0) return null;
            return (
              <View key={tool.id} style={[styles.partitionSegment, { width: `${pct}%`, backgroundColor: tool.color }]} />
            );
          })}
          {freeSpace > 0 && (
            <View style={[styles.partitionSegment, { width: `${(freeSpace / usbSize) * 100}%`, backgroundColor: '#161e30' }]} />
          )}
        </View>
        <View style={styles.partitionLabels}>
          <Text style={[styles.recipeLabel, { fontSize: 11 }]}><Text style={{ color: BLUE }}>■</Text> Allocated: {totalSelected.toFixed(1)} GB</Text>
          <Text style={[styles.recipeLabel, { fontSize: 11 }]}><Text style={{ color: '#161e30' }}>■</Text> Unallocated: {freeSpace.toFixed(1)} GB</Text>
        </View>
      </View>
    );
  }

  function renderStep4() {
    if (!recipe) {
      return (
        <View style={styles.centerFlex}>
          <Text style={[styles.cardTitle, { color: MUTED }]}>Building recipe…</Text>
        </View>
      );
    }
    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={[styles.card, { borderColor: BLUE + '40' }]}>
          <Text style={[styles.recipeTitle, { color: BLUE }]}>📋 {recipe.name}</Text>
          <View style={styles.recipeGrid}>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Device Type</Text>
              <Text style={styles.recipeValue}>{recipe.deviceType}</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Target USB</Text>
              <Text style={styles.recipeValue}>{recipe.targetDevice?.name ?? 'None'}</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Total Size</Text>
              <Text style={[styles.recipeValue, { color: GOLD }]}>{recipe.totalSizeGB.toFixed(1)} GB</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Est. Time</Text>
              <Text style={[styles.recipeValue, { color: CYAN }]}>~{recipe.estimatedMinutes} min</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Partition</Text>
              <Text style={styles.recipeValue}>{recipe.partitionScheme.toUpperCase()}</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Bootloader</Text>
              <Text style={styles.recipeValue}>{recipe.bootloader.toUpperCase()}</Text>
            </View>
          </View>
        </View>

        {renderPartitionBar()}

        {recipe.selectedOS.length > 0 && (
          <View style={[styles.card, { marginTop: 12 }]}>
            <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Operating Systems (Adjust Sizing)</Text>
            {recipe.selectedOS.map(os => (
              <View key={os.id} style={[styles.listRow, { borderLeftColor: os.color, borderLeftWidth: 3, alignItems: 'center' }]}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.listRowName, { color: '#fff' }]}>{os.name}</Text>
                  <Text style={[styles.listRowSize, { color: MUTED }]}>{formatSize(os.sizeGB)}</Text>
                </View>
                {/* Plus / Minus adjust triggers */}
                <View style={styles.adjustControlRow}>
                  <TouchableOpacity onPress={() => adjustOSSize(os.id, -0.5)} style={styles.adjustBtn}>
                    <Text style={styles.adjustText}>-</Text>
                  </TouchableOpacity>
                  <Text style={styles.adjustValue}>{os.sizeGB.toFixed(1)}G</Text>
                  <TouchableOpacity onPress={() => adjustOSSize(os.id, 0.5)} style={styles.adjustBtn}>
                    <Text style={styles.adjustText}>+</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}

        {recipe.selectedTools.length > 0 && (
          <View style={[styles.card, { marginTop: 12 }]}>
            <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Tools</Text>
            {recipe.selectedTools.map(tool => (
              <View key={tool.id} style={[styles.listRow, { borderLeftColor: tool.color, borderLeftWidth: 3 }]}>
                <Text style={[styles.listRowName, { color: '#fff' }]}>{tool.name}</Text>
                <Text style={[styles.listRowSize, { color: MUTED }]}>{formatSize(tool.sizeGB)}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Offline Recipe QR Code Sync Map */}
        {qrUri && (
          <View style={[styles.card, { marginTop: 12, alignItems: 'center' }]}>
            <Text style={[styles.sectionTitle, { color: BLUE, marginBottom: 4 }]}>📲 Sync Recipe to Desktop</Text>
            <Text style={[styles.cardDesc, { color: MUTED, textAlign: 'center', marginBottom: 12 }]}>Scan this QR Code in the PyQt6 Desktop App to import instantly.</Text>
            <Image source={{ uri: qrUri }} style={styles.qrImage} />
          </View>
        )}

        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  }

  function renderStep5() {
    if (!validation) {
      return (
        <View style={styles.centerFlex}>
          <Text style={[styles.cardTitle, { color: MUTED }]}>Validating…</Text>
        </View>
      );
    }
    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={[styles.card, { borderColor: validation.valid ? '#22c55e40' : '#ef444440' }]}>
          <Text style={[styles.recipeTitle, { color: validation.valid ? '#22c55e' : '#ef4444' }]}>
            {validation.valid ? '✅ Recipe Valid' : '❌ Issues Found'}
          </Text>
          <View style={styles.recipeGrid}>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Total Size</Text>
              <Text style={[styles.recipeValue, { color: GOLD }]}>{validation.totalSizeGB.toFixed(1)} GB</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Device Size</Text>
              <Text style={styles.recipeValue}>{validation.deviceSizeGB} GB</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Free After</Text>
              <Text style={[styles.recipeValue, { color: validation.spaceFreeGB > 2 ? '#22c55e' : GOLD }]}>{validation.spaceFreeGB.toFixed(1)} GB</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Est. Time</Text>
              <Text style={[styles.recipeValue, { color: CYAN }]}>{validation.estimatedTime}</Text>
            </View>
          </View>
        </View>

        <View style={[styles.card, { marginTop: 12 }]}>
          <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Checks</Text>
          {validation.checks.map((check, i) => {
            const icon = check.status === 'pass' ? '✅' : check.status === 'warn' ? '⚠️' : '❌';
            const color = check.status === 'pass' ? '#22c55e' : check.status === 'warn' ? GOLD : '#ef4444';
            return (
              <View key={i} style={styles.checkRow}>
                <Text style={styles.checkIcon}>{icon}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.checkName, { color }]}>{check.name}</Text>
                  <Text style={styles.checkMsg}>{check.message}</Text>
                </View>
              </View>
            );
          })}
        </View>
        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  }

  function renderStep6() {
    if (!safety) {
      return (
        <View style={styles.centerFlex}>
          <Text style={[styles.cardTitle, { color: MUTED }]}>Loading safety verification…</Text>
        </View>
      );
    }
    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={[styles.card, { borderColor: '#f9731650', backgroundColor: '#f9731608' }]}>
          <Text style={[styles.recipeTitle, { color: '#f97316' }]}>⚠️ CRITICAL WARNING</Text>
          <Text style={[styles.cardDesc, { color: '#ffffff', fontSize: 13, marginTop: 4, fontWeight: 'bold' }]}>
            Flashing will completely erase all data on the target USB device:
          </Text>
          <Text style={[styles.cardDesc, { color: GOLD, fontSize: 15, marginTop: 6, fontWeight: 'bold' }]}>
            {recipe?.targetDevice?.name} ({recipe?.targetDevice?.path})
          </Text>
        </View>

        <View style={[styles.card, { marginTop: 12 }]}>
          <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Safety Checks</Text>
          {safety.checks.map((check, i) => {
            const icon = check.status === 'pass' ? '✅' : check.status === 'warn' ? '⚠️' : '❌';
            const color = check.status === 'pass' ? '#22c55e' : check.status === 'warn' ? GOLD : '#ef4444';
            return (
              <View key={i} style={styles.checkRow}>
                <Text style={styles.checkIcon}>{icon}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.checkName, { color }]}>{check.name}</Text>
                  <Text style={styles.checkMsg}>{check.message}</Text>
                </View>
              </View>
            );
          })}
        </View>

        <View style={[styles.card, { marginTop: 12, borderColor: BLUE + '40' }]}>
          <Text style={[styles.sectionTitle, { color: BLUE, marginBottom: 8 }]}>🔒 Confirmation Required</Text>
          <Text style={[styles.cardDesc, { color: MUTED, marginBottom: 12 }]}>
            Please enter the safety authorization code below to start the flash sequence.
          </Text>
          
          <View style={styles.codeContainer}>
            <Text style={[styles.codeText, { color: GOLD }]}>{safety.confirmationCode}</Text>
          </View>

          <TextInput
            placeholder="Type verification code here"
            placeholderTextColor={MUTED + '80'}
            style={styles.codeInput}
            value={confirmInput}
            onChangeText={setConfirmInput}
            keyboardType="number-pad"
            maxLength={6}
          />
        </View>
        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  }

  function renderStep7() {
    const overallProgress = buildProgress?.overallProgress ?? 0;
    const widthPct = overallProgress + '%';

    return (
      <View style={styles.scrollContent}>
        <View style={[styles.card, { alignItems: 'center', paddingVertical: 32 }]}>
          <Text style={[styles.doneTitle, { color: BLUE }]}>FLASHING DRIVE</Text>
          
          <View style={styles.pulseOrbContainer}>
            <View style={styles.pulseOrbRing} />
            <View style={[styles.pulseOrbRing, { animationDelay: '0.4s' }]} />
            <Text style={styles.pulseOrbProgress}>{Math.round(overallProgress)}%</Text>
          </View>
          
          <Text style={[styles.cardTitle, { color: '#ffffff', marginTop: 12 }]}>
            {buildProgress?.stageName ?? 'Initializing...'}
          </Text>
          <Text style={[styles.cardDesc, { color: MUTED, textAlign: 'center', marginTop: 4, height: 38 }]}>
            {buildProgress?.currentOperation}
          </Text>
        </View>

        <View style={[styles.card, { marginTop: 12 }]}>
          <View style={styles.progressBarBg}>
            <Animated.View style={[styles.progressBarFill, { width: widthPct }]} />
          </View>
          <View style={[styles.rowBetween, { marginTop: 8 }]}>
            <Text style={[styles.recipeLabel, { color: GOLD }]}>
              {buildProgress?.speedMbps && buildProgress.speedMbps > 0 ? `${buildProgress.speedMbps} MB/s` : '—'}
            </Text>
            <Text style={[styles.recipeLabel, { color: CYAN }]}>
              {buildProgress?.etaSeconds ? etaString(buildProgress.etaSeconds) : 'Calculating...'}
            </Text>
          </View>
        </View>

        <View style={[styles.card, { marginTop: 12 }]}>
          <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Deployment Stage logs</Text>
          {recipe && (recipe.ventoyMacMode ? BUILD_STAGES_MAC : BUILD_STAGES).map((st) => {
            const isDone = completedStages.has(st.id);
            const isActive = buildProgress?.stage === st.id;
            const icon = isDone ? '✅' : isActive ? '⚡' : '⚬';
            const color = isDone ? '#22c55e' : isActive ? BLUE : MUTED + '40';
            return (
              <View key={st.id} style={styles.stageLogLine}>
                <Text style={{ color, marginRight: 8, fontSize: 13, fontWeight: 'bold' }}>{icon}</Text>
                <Text style={[styles.stageLogText, { color: isActive ? '#fff' : MUTED, fontWeight: isActive ? 'bold' : 'normal' }]}>
                  {st.name}
                </Text>
              </View>
            );
          })}
        </View>
      </View>
    );
  }

  function renderStep8() {
    const durationSec = buildEndTime > 0 ? Math.round((buildEndTime - buildStartRef) / 1000) : 0;
    const durationStr = durationSec > 60
      ? Math.floor(durationSec / 60) + ' min ' + (durationSec % 60) + ' sec'
      : durationSec + ' sec';
    const totalWritten = recipe ? recipe.totalSizeGB.toFixed(2) + ' GB' : '—';
    const recipeJSON = recipe ? JSON.stringify(recipe, null, 2) : '{}';

    return (
      <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={[styles.card, { alignItems: 'center', paddingVertical: 32, borderColor: BLUE + '40' }]}>
          <Animated.Text style={[styles.bigEmoji, { transform: [{ scale: pulseAnim }] }]}>⚡</Animated.Text>
          <Text style={[styles.doneTitle, { color: BLUE }]}>USB READY!</Text>
          <Text style={[styles.cardDesc, { color: MUTED, textAlign: 'center', marginTop: 6 }]}>
            Your Phoenix USB has been built successfully.
          </Text>
        </View>

        <View style={[styles.card, { marginTop: 12 }]}>
          <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Build Summary</Text>
          <View style={styles.recipeGrid}>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Device</Text>
              <Text style={styles.recipeValue}>{selectedDevice?.name ?? '—'}</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Data Written</Text>
              <Text style={[styles.recipeValue, { color: GOLD }]}>{totalWritten}</Text>
            </View>
            <View style={styles.recipeGridItem}>
              <Text style={styles.recipeLabel}>Build Time</Text>
              <Text style={[styles.recipeValue, { color: CYAN }]}>{durationStr}</Text>
            </View>
          </View>
        </View>

        {(recipe?.selectedOS ?? []).length > 0 && (
          <View style={[styles.card, { marginTop: 12 }]}>
            <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Installed OS</Text>
            {(recipe?.selectedOS ?? []).map(os => (
              <View key={os.id} style={[styles.doneOSBadge, { backgroundColor: os.color + '18', borderColor: os.color + '40' }]}>
                <View style={[styles.doneOSDot, { backgroundColor: os.color }]} />
                <Text style={[styles.doneOSName, { color: os.color }]}>{os.name}</Text>
                <Text style={[styles.listRowSize, { color: MUTED }]}>v{os.version}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Dynamic completed QR Sync payload for post-build desktop logging */}
        {qrUri && (
          <View style={[styles.card, { marginTop: 12, alignItems: 'center' }]}>
            <Text style={[styles.sectionTitle, { color: GOLD, marginBottom: 4 }]}>📋 Finished Recipe Log</Text>
            <Text style={[styles.cardDesc, { color: MUTED, textAlign: 'center', marginBottom: 12 }]}>Scan this QR code to sync this finished build configuration directly with desktop.</Text>
            <Image source={{ uri: qrUri }} style={styles.qrImage} />
          </View>
        )}

        <TouchableOpacity onPress={resetAll} style={[styles.primaryBtn, { backgroundColor: BLUE, marginTop: 20 }]}>
          <Text style={styles.primaryBtnText}>⚡ Build Another USB</Text>
        </TouchableOpacity>

        <View style={[styles.card, { marginTop: 20 }]}>
          <Text style={[styles.sectionTitle, { marginBottom: 10 }]}>Export Recipe</Text>
          <Text style={[styles.cardDesc, { color: MUTED, marginBottom: 10 }]}>
            Copy the JSON below to import into Phoenix Desktop Builder.
          </Text>
          <View style={styles.jsonBox}>
            <Text style={styles.jsonText} selectable>{recipeJSON}</Text>
          </View>
        </View>

        <View style={styles.bottomPadding} />
      </ScrollView>
    );
  }

  // ─── Bottom action bar ───────────────────────────────────────────────────

  function renderBottomBar() {
    if (step === 7) return null; // No back/continue during build

    if (step === 8) return null;

    const canContinue1 = step === 1 && selectedOS.length > 0;
    const canContinue2 = step === 2; // Tools optional
    const canContinue3 = step === 3 && selectedDevice !== null;
    const canContinue4 = step === 4 && recipe !== null;
    const canContinue5 = step === 5 && validation !== null && validation.valid;
    const canContinue6 = step === 6 && safety !== null && confirmInput.trim() === safety?.confirmationCode;

    let canContinue = canContinue1 || canContinue2 || canContinue3 || canContinue4 || canContinue5 || canContinue6;

    let continueLabel = 'Continue';
    if (step === 4) continueLabel = 'Validate Recipe';
    if (step === 5) continueLabel = 'Run Safety Check';
    if (step === 5 && validation && !validation.valid) continueLabel = 'Fix Issues';
    if (step === 6) continueLabel = 'Start Build ⚡';

    function handleContinue() {
      PhoenixAudio.playClick();
      if (step === 1) setStep(2);
      else if (step === 2) setStep(3);
      else if (step === 3) setStep(4);
      else if (step === 4) handleValidate();
      else if (step === 5) {
        if (validation && !validation.valid) {
          setStep(1);
        } else {
          handleSafetyCheck();
        }
      } else if (step === 6) {
        setStep(7);
      }
    }

    return (
      <View style={styles.bottomBar}>
        {step > 1 && (
          <TouchableOpacity onPress={() => { PhoenixAudio.playClick(); setStep(prev => prev - 1); }} style={styles.backBtn}>
            <Text style={styles.backBtnText}>Back</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          onPress={handleContinue}
          disabled={!canContinue}
          style={[styles.continueBtn, { backgroundColor: canContinue ? BLUE : BLUE + '40', flex: step > 1 ? 1 : undefined, width: step === 1 ? '100%' : undefined }]}>
          <Text style={styles.continueBtnText}>{continueLabel}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ─── Main Render ─────────────────────────────────────────────────────────

  let activeStepContent = renderStep1();
  if (step === 2) activeStepContent = renderStep2();
  else if (step === 3) activeStepContent = renderStep3();
  else if (step === 4) activeStepContent = renderStep4();
  else if (step === 5) activeStepContent = renderStep5();
  else if (step === 6) activeStepContent = renderStep6();
  else if (step === 7) activeStepContent = renderStep7();
  else if (step === 8) activeStepContent = renderStep8();

  return (
    <ScreenContainer style={{ backgroundColor: BG }}>
      <StepIndicator currentStep={step} />
      <View style={styles.contentBox}>
        {activeStepContent}
      </View>
      {renderBottomBar()}
    </ScreenContainer>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  stepRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
    backgroundColor: CARD,
  },
  stepItem: {
    flex: 1,
    alignItems: 'center',
    position: 'relative',
  },
  stepLine: {
    position: 'absolute',
    left: '-50%',
    right: '50%',
    top: 7,
    height: 2,
    zIndex: -1,
  },
  stepDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    marginBottom: 4,
  },
  stepLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  contentBox: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  centerFlex: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '800',
    color: '#fff',
    letterSpacing: 1,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  card: {
    backgroundColor: CARD,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: BORDER,
    padding: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
  },
  cardBody: {
    flex: 1,
    marginLeft: 12,
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '700',
  },
  cardDesc: {
    fontSize: 12,
    color: MUTED,
    marginTop: 4,
    lineHeight: 16,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkMark: {
    color: BG,
    fontSize: 12,
    fontWeight: '900',
  },
  badgeRow: {
    flexDirection: 'row',
    marginTop: 6,
    flexWrap: 'wrap',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
    marginRight: 6,
    marginBottom: 4,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '800',
  },
  radio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: BLUE,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  refreshBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  refreshBtnText: {
    fontSize: 13,
    fontWeight: '700',
  },
  recipeTitle: {
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 12,
  },
  recipeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  recipeGridItem: {
    width: '50%',
    marginBottom: 10,
  },
  recipeLabel: {
    fontSize: 11,
    color: MUTED,
    fontWeight: '600',
  },
  recipeValue: {
    fontSize: 14,
    color: '#fff',
    fontWeight: '700',
    marginTop: 2,
  },
  listRow: {
    backgroundColor: BG,
    borderRadius: 6,
    padding: 10,
    marginBottom: 6,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  listRowName: {
    fontSize: 13,
    fontWeight: '700',
  },
  listRowSize: {
    fontSize: 12,
  },
  checkRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  checkIcon: {
    fontSize: 14,
    marginRight: 8,
    marginTop: 2,
  },
  checkName: {
    fontSize: 13,
    fontWeight: '700',
  },
  checkMsg: {
    fontSize: 11,
    color: MUTED,
    marginTop: 2,
  },
  codeContainer: {
    backgroundColor: BG,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: BORDER,
    paddingVertical: 14,
    alignItems: 'center',
    marginVertical: 10,
  },
  codeText: {
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: 6,
  },
  codeInput: {
    backgroundColor: BG,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: BORDER,
    color: '#fff',
    height: 48,
    paddingHorizontal: 14,
    fontSize: 16,
    textAlign: 'center',
    fontWeight: '700',
    letterSpacing: 2,
  },
  pulseOrbContainer: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: CARD,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 20,
    position: 'relative',
    borderWidth: 2,
    borderColor: BLUE + '30',
  },
  pulseOrbRing: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: 70,
    borderWidth: 1,
    borderColor: BLUE,
    opacity: 0.15,
  },
  pulseOrbProgress: {
    fontSize: 32,
    fontWeight: '900',
    color: BLUE,
  },
  progressBarBg: {
    height: 8,
    backgroundColor: BG,
    borderRadius: 4,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: BORDER,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: BLUE,
  },
  stageLogLine: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
  },
  stageLogText: {
    fontSize: 12,
  },
  bigEmoji: {
    fontSize: 64,
    marginBottom: 8,
  },
  doneTitle: {
    fontSize: 22,
    fontWeight: '900',
    letterSpacing: 1,
  },
  doneOSBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    borderRadius: 6,
    borderWidth: 1,
    marginBottom: 6,
  },
  doneOSDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  doneOSName: {
    fontSize: 13,
    fontWeight: '700',
    flex: 1,
  },
  primaryBtn: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryBtnText: {
    color: BG,
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  jsonBox: {
    backgroundColor: BG,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: BORDER,
    padding: 10,
    maxHeight: 160,
  },
  jsonText: {
    color: MUTED,
    fontSize: 10,
    fontFamily: 'monospace',
  },
  bottomBar: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: BORDER,
    backgroundColor: CARD,
  },
  backBtn: {
    height: 48,
    borderRadius: 8,
    borderColor: BORDER,
    borderWidth: 1,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  backBtnText: {
    color: MUTED,
    fontSize: 14,
    fontWeight: '700',
  },
  continueBtn: {
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  continueBtnText: {
    color: BG,
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  bottomPadding: {
    height: 60,
  },
  shimmerContainer: {
    padding: 14,
    backgroundColor: CARD,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: BORDER,
  },
  shimmerBar: {
    height: 12,
    backgroundColor: '#111827',
    borderRadius: 4,
    width: '90%',
  },
  // Custom Slider styles
  partitionBarContainer: {
    flexDirection: 'row',
    height: 20,
    borderRadius: 5,
    overflow: 'hidden',
    backgroundColor: BG,
    borderWidth: 1,
    borderColor: BORDER,
    marginVertical: 6,
  },
  partitionSegment: {
    height: '100%',
  },
  partitionLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  adjustControlRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  adjustBtn: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: CARD,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: BORDER,
  },
  adjustText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '800',
  },
  adjustValue: {
    color: GOLD,
    fontSize: 12,
    fontWeight: '800',
    marginHorizontal: 8,
    width: 40,
    textAlign: 'center',
  },
  // Custom Importer styles
  customImporterCard: {
    marginTop: 16,
    flexDirection: 'column',
    alignItems: 'stretch',
    borderColor: PURPLE + '30',
    backgroundColor: PURPLE + '03',
  },
  customInput: {
    backgroundColor: BG,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: BORDER,
    color: '#fff',
    height: 38,
    paddingHorizontal: 12,
    fontSize: 13,
    marginBottom: 8,
  },
  customSelectBox: {
    height: 38,
    backgroundColor: BG,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: BORDER,
    width: 90,
    justifyContent: 'center',
    marginBottom: 8,
  },
  selectToggle: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  selectToggleText: {
    color: GOLD,
    fontSize: 11,
    fontWeight: '800',
  },
  qrImage: {
    width: 200,
    height: 200,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: BORDER,
  },
});
