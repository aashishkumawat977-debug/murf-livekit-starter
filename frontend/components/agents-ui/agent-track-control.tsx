'use client';

import { useEffect, useMemo, useState } from 'react';
import { type VariantProps, cva } from 'class-variance-authority';
import { LocalAudioTrack, LocalVideoTrack } from 'livekit-client';

import {
  type TrackReferenceOrPlaceholder,
  useMaybeRoomContext,
  useMediaDeviceSelect,
} from '@livekit/components-react';

import { AgentAudioVisualizerBar } from '@/components/agents-ui/agent-audio-visualizer-bar';
import { AgentTrackToggle } from '@/components/agents-ui/agent-track-toggle';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

import { cn } from '@/lib/shadcn/utils';

const selectVariants = cva(
  [
    'rounded-l-none',
    'shadow-none',
    'pl-2',
    'text-foreground',
    'hover:text-muted-foreground',
    'peer-data-[state=on]/track:bg-muted',
    'peer-data-[state=on]/track:hover:bg-foreground/10',
    'peer-data-[state=off]/track:text-destructive',
    'peer-data-[state=off]/track:focus-visible:border-destructive',
    'peer-data-[state=off]/track:focus-visible:ring-destructive/30',
    '[&_svg]:opacity-100',
  ],
  {
    variants: {
      variant: {
        default: [
          'border-none',
          'peer-data-[state=off]/track:bg-destructive/10',
          'peer-data-[state=off]/track:hover:bg-destructive/15',
          'peer-data-[state=off]/track:[&_svg]:text-destructive!',

          'dark:peer-data-[state=on]/track:bg-accent',
          'dark:peer-data-[state=on]/track:hover:bg-foreground/10',
          'dark:peer-data-[state=off]/track:bg-destructive/10',
          'dark:peer-data-[state=off]/track:hover:bg-destructive/15',
        ],

        outline: [
          'border',
          'border-l-0',
          'peer-data-[state=off]/track:border-destructive/20',
          'peer-data-[state=off]/track:bg-destructive/10',
          'peer-data-[state=off]/track:hover:bg-destructive/15',
          'peer-data-[state=off]/track:[&_svg]:text-destructive!',
          'peer-data-[state=on]/track:hover:border-foreground/12',

          'dark:peer-data-[state=off]/track:bg-destructive/10',
          'dark:peer-data-[state=off]/track:hover:bg-destructive/15',
          'dark:peer-data-[state=on]/track:bg-accent',
          'dark:peer-data-[state=on]/track:hover:bg-foreground/10',
        ],
      },

      size: {
        default: 'w-[180px]',
        sm: 'w-auto',
      },
    },

    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

type TrackDeviceSelectProps = React.ComponentProps<
  typeof SelectTrigger
> &
  VariantProps<typeof selectVariants> & {
    kind: MediaDeviceKind;
    track?: LocalAudioTrack | LocalVideoTrack;
    requestPermissions?: boolean;
    onMediaDeviceError?: (error: Error) => void;
    onDeviceListChange?: (devices: MediaDeviceInfo[]) => void;
    onActiveDeviceChange?: (deviceId: string) => void;
  };

function TrackDeviceSelect({
  kind,
  track,
  size = 'default',
  variant = 'default',
  className,
  requestPermissions = false,
  onMediaDeviceError,
  onDeviceListChange,
  onActiveDeviceChange,
  ...props
}: TrackDeviceSelectProps) {
  const room = useMaybeRoomContext();

  const [open, setOpen] = useState(false);
  const [requestPermissionsState, setRequestPermissionsState] =
    useState(requestPermissions);

  const {
    devices,
    activeDeviceId,
    setActiveMediaDevice,
  } = useMediaDeviceSelect({
    room,
    kind,
    track,
    requestPermissions: requestPermissionsState,
    onError: onMediaDeviceError,
  });

  useEffect(() => {
    onDeviceListChange?.(devices);
  }, [devices, onDeviceListChange]);

  const filteredDevices = useMemo(
    () => devices.filter((device) => device.deviceId !== ''),
    [devices]
  );

  /*
   * Only show the arrow when there is actually more than
   * one device available.
   */
  if (filteredDevices.length < 2) {
    return null;
  }

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);

    if (nextOpen) {
      setRequestPermissionsState(true);
    }
  };

  const handleValueChange = (deviceId: string) => {
    if (!deviceId) {
      return;
    }

    setActiveMediaDevice(deviceId);
    onActiveDeviceChange?.(deviceId);

    /*
     * Close immediately after selecting a device.
     * This prevents the dropdown from flashing/reopening
     * during the LiveKit device update.
     */
    setOpen(false);
  };

  return (
    <Select
      open={open}
      onOpenChange={handleOpenChange}
      value={activeDeviceId ?? ''}
      onValueChange={handleValueChange}
    >
      <SelectTrigger
        {...props}
        className={cn(
          selectVariants({
            size,
            variant,
          }),
          className
        )}
      >
        {size !== 'sm' && (
          <SelectValue
            className="font-mono text-sm"
            placeholder={`Select a ${kind}`}
          />
        )}
      </SelectTrigger>

      <SelectContent
        position="popper"
        side="top"
        align="start"
        sideOffset={8}
        className="z-[100]"
      >
        {filteredDevices.map((device) => (
          <SelectItem
            key={device.deviceId}
            value={device.deviceId}
          >
            {device.label || `Unknown ${kind}`}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export type AgentTrackControlProps =
  VariantProps<typeof selectVariants> & {
    kind: MediaDeviceKind;
    source: 'camera' | 'microphone' | 'screen_share';
    pressed?: boolean;
    pending?: boolean;
    disabled?: boolean;
    className?: string;
    audioTrack?: TrackReferenceOrPlaceholder;
    onPressedChange?: (pressed: boolean) => void;
    onMediaDeviceError?: (error: Error) => void;
    onActiveDeviceChange?: (deviceId: string) => void;
  };

export function AgentTrackControl({
  kind,
  variant = 'default',
  source,
  pressed,
  pending,
  disabled,
  className,
  audioTrack,
  onPressedChange,
  onMediaDeviceError,
  onActiveDeviceChange,
}: AgentTrackControlProps) {
  return (
    <div
      className={cn(
        'relative flex h-10 min-w-0 shrink-0 items-center gap-0 rounded-md',
        variant === 'outline' &&
          'shadow-xs [&_button]:shadow-none',
        className
      )}
    >
      <AgentTrackToggle
        variant={variant ?? 'default'}
        source={source}
        pressed={pressed}
        pending={pending}
        disabled={disabled}
        onPressedChange={onPressedChange}
        className={cn(
          'peer/track group/track',
          'relative z-0 shrink-0',
          'focus:z-10',
          'has-[.audiovisualizer]:w-auto',
          'has-[.audiovisualizer]:px-3',
          'has-[~_button]:rounded-r-none',
          'has-[~_button]:border-r-0',
          'has-[~_button]:pr-2',
          'has-[~_button]:pl-3'
        )}
      >
        {audioTrack && (
          <AgentAudioVisualizerBar
            size="icon"
            barCount={3}
            state={pressed ? 'speaking' : 'disconnected'}
            audioTrack={pressed ? audioTrack : undefined}
            className={cn(
              'audiovisualizer',
              'flex',
              'h-6',
              'w-5',
              'shrink-0',
              'items-center',
              'justify-center',
              'gap-0.5',
              'overflow-hidden'
            )}
          >
            <span
              className={cn(
                'h-full',
                'min-h-0.5',
                'w-0.5',
                'shrink-0',
                'origin-center',
                'group-data-[state=on]/track:bg-foreground',
                'group-data-[state=off]/track:bg-destructive',
                'data-lk-muted:bg-muted'
              )}
            />
          </AgentAudioVisualizerBar>
        )}
      </AgentTrackToggle>

      {kind && (
        <TrackDeviceSelect
          size="sm"
          kind={kind}
          variant={variant}
          requestPermissions={false}
          onMediaDeviceError={onMediaDeviceError}
          onActiveDeviceChange={onActiveDeviceChange}
          className={cn(
            'relative z-10 shrink-0',
            'before:absolute',
            'before:inset-y-0',
            'before:left-0',
            'before:my-2.5',
            'before:w-px',
            'before:bg-border',
            !pressed && 'before:bg-destructive/20'
          )}
        />
      )}
    </div>
  );
}