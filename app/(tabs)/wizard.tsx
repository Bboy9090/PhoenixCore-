import {
  ScrollView,
  Text,
  View,
  Pressable,
  StyleSheet,
  Animated,
} from 'react-native';
import { useState, useEffect, useRef, useMemo } from 'react';
import { useRouter } from 'expo-router';
import { ScreenContainer } from '@/components/screen-container';
import { IconSymbol } from '@/components/ui/icon-symbol';
import { useColors as _useColors } from '@/hooks/use-colors';
import { DEVICE_TYPES, OS_CATALOG, getCompatibility } from '@/lib/data/catalog';
import { detectDevice, detectDeviceAsync, type DeviceProfile } from '@/lib/phoenix-engine';

// ─── Constants ────────────────────────────────────────────────────────────────

const BLUE = '#00d2ff';
const GOLD = '#ffd700';
const CARD = '#0a0e1a';
const MUTED = '#94a3b8';
const SUCCESS = '#22c55e';
const WARN = '#f59e0b';
const ERR = '#ef4444';

type WizardStep = 'detect' | 'scan' | 'compat' | 'launch';

const STEP_ORDER: WizardStep[] = ['detect', 'scan', 'compat', 'launch'];

// ─── Step Indicator ───────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: WizardStep }) {
  const currentIndex = STEP_ORDER.indexOf(current);
  const labels = ['Detect', 'Scan', 'Compatible', 'Build'];

  return (
    <View style={si.row}>
      {labels.map((label, i) => {
        const active = i <= currentIndex;
        const isCurrent = i === currentIndex;
        return (
          <View key={label} style={si.item}>
            <View
              style={[
                si.dot,
                { backgroundColor: active ? BLUE : MUTED + '44' },
                isCurrent && { shadowColor: BLUE, shadowOpacity: 0.8, shadowRadius: 6, elevation: 4 },
              ]}
            >
              {active && i < currentIndex && (
                <Text style={si.dotCheck}>✓</Text>
              )}
              {isCurrent && <View style={si.dotInner} />}
            </View>
            <Text style={[si.label, { color: active ? BLUE : MUTED }]}>{label}</Text>
            {i < labels.length - 1 && (
              <View style={[si.line, { backgroundColor: i < currentIndex ? BLUE : MUTED + '33' }]} />
            )}
          </View>
        );
      })}
    </View>
  );
}

const si = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingHorizontal: 20,
    marginTop: 14,
    marginBottom: 4,
  },
  item: {
    flex: 1,
    alignItems: 'center',
    position: 'relative',
  },
  dot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  dotInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#fff',
  },
  dotCheck: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '700',
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.4,
    textAlign: 'center',
  },
  line: {
    position: 'absolute',
    top: 14,
    left: '60%',
    right: '-60%',
    height: 2,
    zIndex: -1,
  },
});

// ─── Step 1: Detect ───────────────────────────────────────────────────────────

function StepDetect({
  onSelect,
}: {
  onSelect: (deviceId: string, profile?: DeviceProfile) => void;
}) {
  const [scanning, setScanning] = useState(false);
  const [detectedMsg, setDetectedMsg] = useState<string | null>(null);
  const scanAnim = useRef(new Animated.Value(0)).current;
  const scanLoop = useRef<Animated.CompositeAnimation | null>(null);

  const startScan = () => {
    setScanning(true);
    setDetectedMsg(null);

    scanLoop.current = Animated.loop(
      Animated.sequence([
        Animated.timing(scanAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
        Animated.timing(scanAnim, { toValue: 0.3, duration: 500, useNativeDriver: true }),
      ])
    );
    scanLoop.current.start();

    setTimeout(async () => {
      scanLoop.current?.stop();
      scanAnim.setValue(0);
      const profile = await detectDeviceAsync();
      const match = DEVICE_TYPES.find((d) => d.id === profile.deviceType);
      setScanning(false);
      setDetectedMsg('Detected: ' + (profile.model ?? 'Unknown'));
      if (match) {
        onSelect(match.id, profile);
      }
    }, 1500);
  };

  const cols: [typeof DEVICE_TYPES[number], typeof DEVICE_TYPES[number] | null][] = [];
  for (let i = 0; i < DEVICE_TYPES.length; i += 2) {
    cols.push([DEVICE_TYPES[i], DEVICE_TYPES[i + 1] ?? null]);
  }

  return (
    <View style={styles.section}>
      <Text style={styles.screenTitle}>{'⚡ Device Wizard'}</Text>
      <Text style={[styles.screenSubtitle, { color: MUTED }]}>
        {'Select your device type to check Phoenix OS compatibility'}
      </Text>

      {/* Auto-detect button */}
      <Pressable
        onPress={startScan}
        disabled={scanning}
        style={({ pressed }) => [
          styles.autoDetectBtn,
          { borderColor: GOLD, opacity: pressed || scanning ? 0.75 : 1 },
        ]}
      >
        {scanning ? (
          <Animated.View style={[styles.scanBar, { opacity: scanAnim }]} />
        ) : (
          <View style={styles.autoDetectInner}>
            <Text style={{ fontSize: 16 }}>{'🔍'}</Text>
            <Text style={[styles.autoDetectText, { color: GOLD }]}>{'Auto-Detect My Device'}</Text>
          </View>
        )}
      </Pressable>

      {detectedMsg !== null && (
        <View style={styles.toast}>
          <Text style={[styles.toastText, { color: SUCCESS }]}>{detectedMsg}</Text>
        </View>
      )}

      <Text style={[styles.sectionLabel, { color: MUTED }]}>{'WHAT TYPE OF DEVICE ARE YOU WORKING WITH?'}</Text>

      {cols.map(([a, b], rowIdx) => (
        <View key={rowIdx} style={styles.gridRow}>
          <DeviceCard item={a} onPress={() => onSelect(a.id)} />
          {b ? <DeviceCard item={b} onPress={() => onSelect(b.id)} /> : <View style={styles.gridCell} />}
        </View>
      ))}
    </View>
  );
}

function DeviceCard({
  item,
  onPress,
}: {
  item: typeof DEVICE_TYPES[number];
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.gridCell,
        styles.deviceCard,
        pressed && { opacity: 0.8, transform: [{ scale: 0.97 }] },
      ]}
    >
      <View style={styles.deviceIconWrap}>
        <IconSymbol name={item.icon as any} size={26} color={BLUE} />
      </View>
      <Text style={styles.deviceName} numberOfLines={2}>{item.name}</Text>
      <Text style={[styles.deviceDesc, { color: MUTED }]} numberOfLines={3}>{item.description}</Text>
      <View style={styles.archRow}>
        {item.architectures.map((arch) => (
          <View key={arch} style={styles.archBadge}>
            <Text style={[styles.archText, { color: BLUE }]}>{arch}</Text>
          </View>
        ))}
      </View>
    </Pressable>
  );
}

// ─── Step 2: Hardware Scan ────────────────────────────────────────────────────

const SCAN_FIELDS = [
  { label: 'Platform', key: 'platform' },
  { label: 'Architecture', key: 'architecture' },
  { label: 'Model', key: 'model' },
  { label: 'OS Version', key: 'osVersion' },
  { label: 'Total RAM', key: 'totalMemoryGB' },
] as const;

function StepScan({
  selectedDeviceId,
  profile,
  onContinue,
}: {
  selectedDeviceId: string;
  profile: DeviceProfile | null;
  onContinue: () => void;
}) {
  const [phase, setPhase] = useState<'scanning' | 'done'>('scanning');
  const [visibleCount, setVisibleCount] = useState(0);
  const orbAnim = useRef(new Animated.Value(0.4)).current;
  const orbLoop = useRef<Animated.CompositeAnimation | null>(null);
  const fadeAnims = useRef(SCAN_FIELDS.map(() => new Animated.Value(0))).current;

  const deviceName = DEVICE_TYPES.find((d) => d.id === selectedDeviceId)?.name ?? selectedDeviceId;
  const liveProfile = profile ?? detectDevice();

  useEffect(() => {
    orbLoop.current = Animated.loop(
      Animated.sequence([
        Animated.timing(orbAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
        Animated.timing(orbAnim, { toValue: 0.4, duration: 800, useNativeDriver: true }),
      ])
    );
    orbLoop.current.start();

    const timer = setTimeout(() => {
      orbLoop.current?.stop();
      orbAnim.setValue(1);
      setPhase('done');

      SCAN_FIELDS.forEach((_, i) => {
        setTimeout(() => {
          Animated.timing(fadeAnims[i], {
            toValue: 1,
            duration: 300,
            useNativeDriver: true,
          }).start();
          setVisibleCount((c) => c + 1);
        }, i * 150);
      });
    }, 2000);

    return () => {
      clearTimeout(timer);
      orbLoop.current?.stop();
    };
  }, []);

  const fieldValues: Record<string, string> = {
    platform: liveProfile.platform,
    architecture: liveProfile.architecture,
    model: liveProfile.model,
    osVersion: liveProfile.osVersion,
    totalMemoryGB: liveProfile.totalMemoryGB > 0 ? `${liveProfile.totalMemoryGB} GB` : '8 GB (Offline Fallback)',
  };

  return (
    <View style={styles.section}>
      <Text style={styles.screenTitle}>{'Hardware Scan'}</Text>
      <Text style={[styles.screenSubtitle, { color: MUTED }]}>
        {phase === 'scanning' ? 'Scanning your hardware...' : 'Detection complete'}
      </Text>

      {/* Orb */}
      <View style={styles.orbWrap}>
        <Animated.View style={[styles.orbOuter, { opacity: orbAnim }]}>
          <View style={styles.orbInner}>
            <Text style={{ fontSize: 32 }}>{'⚡'}</Text>
          </View>
        </Animated.View>
        {phase === 'scanning' && (
          <Text style={[styles.scanningText, { color: BLUE }]}>{'Scanning your hardware...'}</Text>
        )}
      </View>

      {phase === 'done' && (
        <View style={styles.scanResults}>
          {SCAN_FIELDS.map((f, i) => (
            <Animated.View
              key={f.key}
              style={[styles.scanRow, { opacity: fadeAnims[i] }]}
            >
              <Text style={[styles.scanLabel, { color: MUTED }]}>{f.label}</Text>
              <View style={styles.scanValueRow}>
                <Text style={[styles.checkmark, { color: SUCCESS }]}>{'✓'}</Text>
                <Text style={[styles.scanValue, { color: '#fff' }]}>
                  {fieldValues[f.key] ?? '—'}
                </Text>
              </View>
            </Animated.View>
          ))}

          {/* Device type row */}
          <Animated.View style={[styles.scanRow, { opacity: visibleCount >= SCAN_FIELDS.length ? 1 : 0 }]}>
            <Text style={[styles.scanLabel, { color: MUTED }]}>{'Device Type'}</Text>
            <View style={styles.scanValueRow}>
              <Text style={[styles.checkmark, { color: SUCCESS }]}>{'✓'}</Text>
              <Text style={[styles.scanValue, { color: BLUE }]}>{deviceName}</Text>
            </View>
          </Animated.View>

          <Pressable
            onPress={onContinue}
            style={({ pressed }) => [
              styles.ctaBtn,
              { backgroundColor: BLUE, opacity: pressed ? 0.85 : 1 },
            ]}
          >
            <Text style={styles.ctaBtnText}>{'Continue to Compatibility'}</Text>
            <IconSymbol name="chevron.right" size={18} color="#fff" />
          </Pressable>
        </View>
      )}
    </View>
  );
}

// ─── Step 3: Compatibility ────────────────────────────────────────────────────

function StepCompat({
  selectedDeviceId,
  onBuild,
}: {
  selectedDeviceId: string;
  onBuild: () => void;
}) {
  const device = DEVICE_TYPES.find((d) => d.id === selectedDeviceId);
  const compatibility = useMemo(() => getCompatibility(selectedDeviceId), [selectedDeviceId]);

  const supported = compatibility.filter((c) => c.status === 'supported');
  const partial = compatibility.filter((c) => c.status === 'partial');
  const unsupported = compatibility.filter((c) => c.status === 'unsupported');

  return (
    <View style={styles.section}>
      <Text style={styles.screenTitle}>{'Compatibility Results'}</Text>
      <Text style={[styles.screenSubtitle, { color: MUTED }]}>
        {'for ' + (device?.name ?? selectedDeviceId)}
      </Text>

      {/* Summary stats */}
      <View style={styles.statsRow}>
        <StatChip count={supported.length} label={'Supported'} color={SUCCESS} />
        <StatChip count={partial.length} label={'Partial'} color={WARN} />
        <StatChip count={unsupported.length} label={'Unsupported'} color={ERR} />
      </View>

      {/* Supported */}
      {supported.length > 0 && (
        <View style={styles.compatGroup}>
          <View style={styles.groupHeader}>
            <Text style={[styles.groupHeaderText, { color: SUCCESS }]}>{'✅ SUPPORTED'}</Text>
          </View>
          {supported.map((c) => {
            const os = OS_CATALOG.find((o) => o.id === c.osId);
            if (!os) return null;
            return (
              <CompatCard key={c.osId} os={os} notes={c.notes} status="supported" />
            );
          })}
        </View>
      )}

      {/* Partial */}
      {partial.length > 0 && (
        <View style={styles.compatGroup}>
          <View style={styles.groupHeader}>
            <Text style={[styles.groupHeaderText, { color: WARN }]}>{'⚠️ PARTIAL'}</Text>
          </View>
          {partial.map((c) => {
            const os = OS_CATALOG.find((o) => o.id === c.osId);
            if (!os) return null;
            return (
              <CompatCard key={c.osId} os={os} notes={c.notes} status="partial" />
            );
          })}
        </View>
      )}

      {/* Unsupported */}
      {unsupported.length > 0 && (
        <View style={styles.compatGroup}>
          <View style={styles.groupHeader}>
            <Text style={[styles.groupHeaderText, { color: ERR }]}>{'❌ NOT SUPPORTED'}</Text>
          </View>
          {unsupported.map((c) => {
            const os = OS_CATALOG.find((o) => o.id === c.osId);
            if (!os) return null;
            return (
              <CompatCard key={c.osId} os={os} notes={c.notes} status="unsupported" />
            );
          })}
        </View>
      )}

      <Pressable
        onPress={onBuild}
        style={({ pressed }) => [
          styles.ctaBtn,
          { backgroundColor: BLUE, opacity: pressed ? 0.85 : 1, marginTop: 12 },
        ]}
      >
        <IconSymbol name="externaldrive.fill" size={18} color="#fff" />
        <Text style={styles.ctaBtnText}>{'Build USB for This Device'}</Text>
      </Pressable>
    </View>
  );
}

function StatChip({ count, label, color }: { count: number; label: string; color: string }) {
  return (
    <View style={[styles.statChip, { borderColor: color + '55' }]}>
      <Text style={[styles.statCount, { color }]}>{count}</Text>
      <Text style={[styles.statLabel, { color: MUTED }]}>{label}</Text>
    </View>
  );
}

function CompatCard({
  os,
  notes,
  status,
}: {
  os: (typeof OS_CATALOG)[number];
  notes: string;
  status: 'supported' | 'partial' | 'unsupported';
}) {
  const borderColor =
    status === 'supported' ? SUCCESS : status === 'partial' ? WARN : ERR + '88';
  const badgeColor =
    status === 'supported' ? SUCCESS : status === 'partial' ? WARN : ERR;
  const badgeText =
    status === 'supported' ? '✅ SUPPORTED' : status === 'partial' ? '⚠️ PARTIAL' : '❌ NOT SUPPORTED';

  return (
    <View style={[styles.compatCard, { borderLeftColor: borderColor }]}>
      <View style={styles.compatCardTop}>
        <View style={{ flex: 1 }}>
          <Text style={styles.compatName}>{os.name + ' ' + os.version}</Text>
          <Text style={[styles.compatMeta, { color: MUTED }]}>
            {os.sizeGB + ' GB  ·  ' + os.bootMethod}
          </Text>
        </View>
        <View style={[styles.badge, { backgroundColor: badgeColor + '22', borderColor: badgeColor + '55' }]}>
          <Text style={[styles.badgeText, { color: badgeColor }]}>{badgeText}</Text>
        </View>
      </View>
      <Text style={[styles.compatNotes, { color: MUTED }]}>{notes}</Text>
    </View>
  );
}

// ─── Step 4: Launch ───────────────────────────────────────────────────────────

function StepLaunch() {
  const router = useRouter();
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.3, duration: 400, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 400, useNativeDriver: true }),
      ])
    );
    loop.start();

    const nav = setTimeout(() => {
      loop.stop();
      router.push('/(tabs)/builder');
    }, 1000);

    return () => {
      loop.stop();
      clearTimeout(nav);
    };
  }, []);

  return (
    <View style={[styles.section, styles.launchCenter]}>
      <Animated.Text
        style={[styles.launchEmoji, { transform: [{ scale: pulseAnim }] }]}
      >
        {'⚡'}
      </Animated.Text>
      <Text style={styles.launchTitle}>{'Launching USB Builder...'}</Text>
      <Text style={[styles.screenSubtitle, { color: MUTED, textAlign: 'center' }]}>
        {'Taking you to the builder with your device profile loaded'}
      </Text>
    </View>
  );
}

// ─── Main Screen ──────────────────────────────────────────────────────────────

export default function WizardScreen() {
  const [step, setStep] = useState<WizardStep>('detect');
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [deviceProfile, setDeviceProfile] = useState<DeviceProfile | null>(null);

  const handleDetect = (deviceId: string, profile?: DeviceProfile) => {
    setSelectedDeviceId(deviceId);
    if (profile) setDeviceProfile(profile);
    setStep('scan');
  };

  const handleScanDone = () => {
    setStep('compat');
  };

  const handleBuild = () => {
    setStep('launch');
  };

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
      >
        <StepIndicator current={step} />

        {step === 'detect' && (
          <StepDetect onSelect={handleDetect} />
        )}

        {step === 'scan' && selectedDeviceId !== null && (
          <StepScan
            selectedDeviceId={selectedDeviceId}
            profile={deviceProfile}
            onContinue={handleScanDone}
          />
        )}

        {step === 'compat' && selectedDeviceId !== null && (
          <StepCompat
            selectedDeviceId={selectedDeviceId}
            onBuild={handleBuild}
          />
        )}

        {step === 'launch' && <StepLaunch />}
      </ScrollView>
    </ScreenContainer>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  section: {
    paddingHorizontal: 16,
    marginTop: 12,
    gap: 10,
  },
  screenTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: BLUE,
    marginBottom: 2,
  },
  screenSubtitle: {
    fontSize: 14,
    lineHeight: 20,
    color: MUTED,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginTop: 6,
    marginBottom: 2,
  },

  // Auto-detect button
  autoDetectBtn: {
    borderWidth: 1.5,
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: GOLD + '0f',
    minHeight: 52,
  },
  autoDetectInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  autoDetectText: {
    fontSize: 15,
    fontWeight: '700',
  },
  scanBar: {
    width: '70%',
    height: 4,
    borderRadius: 2,
    backgroundColor: GOLD,
  },

  // Toast
  toast: {
    backgroundColor: SUCCESS + '18',
    borderWidth: 1,
    borderColor: SUCCESS + '44',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 14,
  },
  toastText: {
    fontSize: 13,
    fontWeight: '600',
  },

  // Grid
  gridRow: {
    flexDirection: 'row',
    gap: 10,
  },
  gridCell: {
    flex: 1,
  },
  deviceCard: {
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BLUE + '28',
    borderRadius: 14,
    padding: 14,
    gap: 6,
  },
  deviceIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: BLUE + '18',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 2,
  },
  deviceName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#fff',
  },
  deviceDesc: {
    fontSize: 11,
    lineHeight: 16,
  },
  archRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 2,
  },
  archBadge: {
    backgroundColor: BLUE + '18',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 5,
  },
  archText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.3,
  },

  // Scan orb
  orbWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 28,
    gap: 16,
  },
  orbOuter: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: BLUE + '22',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: BLUE,
    shadowOpacity: 0.8,
    shadowRadius: 24,
    elevation: 10,
  },
  orbInner: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: BLUE + '33',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scanningText: {
    fontSize: 15,
    fontWeight: '600',
  },

  // Scan results
  scanResults: {
    gap: 8,
  },
  scanRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: CARD,
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderWidth: 1,
    borderColor: BLUE + '20',
  },
  scanLabel: {
    fontSize: 13,
    fontWeight: '600',
  },
  scanValueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  checkmark: {
    fontSize: 14,
    fontWeight: '700',
  },
  scanValue: {
    fontSize: 13,
    fontWeight: '600',
  },

  // CTA button
  ctaBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 14,
    gap: 8,
    marginTop: 4,
  },
  ctaBtnText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },

  // Stats row
  statsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  statChip: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
    borderRadius: 10,
    borderWidth: 1,
    backgroundColor: CARD,
    gap: 2,
  },
  statCount: {
    fontSize: 22,
    fontWeight: '800',
  },
  statLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.4,
  },

  // Compat groups
  compatGroup: {
    gap: 6,
  },
  groupHeader: {
    marginTop: 6,
    marginBottom: 2,
  },
  groupHeaderText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  compatCard: {
    backgroundColor: CARD,
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 3,
    borderColor: '#ffffff10',
    padding: 12,
    gap: 6,
  },
  compatCardTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  compatName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#fff',
  },
  compatMeta: {
    fontSize: 11,
    marginTop: 2,
  },
  badge: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.4,
  },
  compatNotes: {
    fontSize: 12,
    lineHeight: 17,
  },

  // Launch
  launchCenter: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 60,
    gap: 18,
  },
  launchEmoji: {
    fontSize: 72,
    textAlign: 'center',
  },
  launchTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: BLUE,
    textAlign: 'center',
  },
});
