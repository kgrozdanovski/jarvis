<template>
  <component
    :is="resolvedIcon"
    aria-hidden="true"
    class="assistant-icon"
    :size="size"
    :stroke-width="stroke"
  />
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import {
  Activity,
  ArrowUp,
  BellOff,
  Brain,
  Briefcase,
  CalendarClock,
  CalendarDays,
  Check,
  Circle,
  Clock3,
  CloudSun,
  Coffee,
  Cpu,
  Database,
  GitBranch,
  HardDrive,
  History,
  Home,
  Images,
  LayoutTemplate,
  Lightbulb,
  ListChecks,
  Lock,
  MapPin,
  MessageSquare,
  Mic,
  Monitor,
  Moon,
  Package,
  Plane,
  PlugZap,
  Radio,
  RotateCcw,
  Router as RouterIcon,
  Rocket,
  ScanSearch,
  Search,
  Server,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Smartphone,
  Sparkles,
  Speaker,
  Square,
  Sun,
  Sunrise,
  Thermometer,
  Tv,
  User,
  Users,
  Video,
  Volume2,
  Wifi,
  X,
  Zap
} from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    name?: string
    size?: number
    stroke?: number
  }>(),
  {
    name: 'circle',
    size: 20,
    stroke: 1.8
  }
)

const iconMap: Record<string, Component> = {
  activity: Activity,
  'arrow-up': ArrowUp,
  'bell-off': BellOff,
  brain: Brain,
  briefcase: Briefcase,
  'calendar-clock': CalendarClock,
  'calendar-days': CalendarDays,
  check: Check,
  circle: Circle,
  clock: Clock3,
  'cloud-sun': CloudSun,
  coffee: Coffee,
  cpu: Cpu,
  database: Database,
  'git-branch': GitBranch,
  'hard-drive': HardDrive,
  history: History,
  home: Home,
  images: Images,
  'layout-template': LayoutTemplate,
  lightbulb: Lightbulb,
  'list-checks': ListChecks,
  lock: Lock,
  'map-pin': MapPin,
  'message-square': MessageSquare,
  mic: Mic,
  monitor: Monitor,
  moon: Moon,
  package: Package,
  plane: Plane,
  'plug-zap': PlugZap,
  radio: Radio,
  'rotate-ccw': RotateCcw,
  router: RouterIcon,
  rocket: Rocket,
  'scan-search': ScanSearch,
  search: Search,
  server: Server,
  settings: Settings,
  'shield-check': ShieldCheck,
  'sliders-horizontal': SlidersHorizontal,
  smartphone: Smartphone,
  sparkles: Sparkles,
  speaker: Speaker,
  square: Square,
  sun: Sun,
  sunrise: Sunrise,
  thermometer: Thermometer,
  tv: Tv,
  user: User,
  users: Users,
  video: Video,
  'volume-2': Volume2,
  wifi: Wifi,
  x: X,
  zap: Zap
}

const resolvedIcon = computed(() => iconMap[props.name] ?? Circle)
</script>
