import React, { useMemo } from 'react';
import { Track } from 'livekit-client';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  type TrackReference,
  VideoTrack,
  useLocalParticipant,
  useTracks,
  useVoiceAssistant,
} from '@livekit/components-react';
import { cn } from '@/lib/shadcn/utils';
import { AudioVisualizer } from './audio-visualizer';

const ANIMATION_TRANSITION: MotionProps['transition'] = {
  type: 'spring',
  stiffness: 675,
  damping: 75,
  mass: 1,
};

const tileViewClassNames = {
  grid: [
    'h-full w-full',
    'grid gap-x-2 place-content-center',
    'grid-cols-[1fr_1fr] grid-rows-[90px_1fr_90px]',
  ],

  agentChatOpenWithSecondTile: [
    'col-start-1 row-start-1',
    'self-center justify-self-end',
  ],

  agentChatOpenWithoutSecondTile: [
    'col-start-1 row-start-1',
    'col-span-2',
    'place-content-center',
  ],

  agentChatClosed: [
    'col-start-1 row-start-1',
    'col-span-2 row-span-3',
    'place-content-center',
  ],

  secondTileChatOpen: [
    'col-start-2 row-start-1',
    'self-center justify-self-start',
  ],

  secondTileChatClosed: [
    'col-start-2 row-start-3',
    'place-content-end',
  ],
};

export function useLocalTrackRef(source: Track.Source) {
  const { localParticipant } = useLocalParticipant();

  const publication = localParticipant.getTrackPublication(source);

  const trackRef = useMemo<TrackReference | undefined>(
    () =>
      publication
        ? {
            source,
            participant: localParticipant,
            publication,
          }
        : undefined,
    [source, publication, localParticipant]
  );

  return trackRef;
}

interface TileLayoutProps {
  chatOpen: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerWaveLineWidth?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerBarCount?: number;
}

export function TileLayout({
  chatOpen,
  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerWaveLineWidth,
}: TileLayoutProps) {
  const {
    videoTrack: agentVideoTrack,
    state,
  } = useVoiceAssistant();

  const [screenShareTrack] = useTracks([
    Track.Source.ScreenShare,
  ]);

  const cameraTrack: TrackReference | undefined =
    useLocalTrackRef(Track.Source.Camera);

  const isCameraEnabled =
    cameraTrack && !cameraTrack.publication.isMuted;

  const isScreenShareEnabled =
    screenShareTrack && !screenShareTrack.publication.isMuted;

  const hasSecondTile =
    isCameraEnabled || isScreenShareEnabled;

  const animationDelay = chatOpen ? 0 : 0.15;

  const isAvatar = agentVideoTrack !== undefined;

  const videoWidth =
    agentVideoTrack?.publication.dimensions?.width ?? 0;

  const videoHeight =
    agentVideoTrack?.publication.dimensions?.height ?? 0;

  const currentState = String(state ?? '').toLowerCase();

  const isListening = currentState === 'listening';
  const isSpeaking = currentState === 'speaking';
  const isThinking = currentState === 'thinking';

  const statusLabel = isSpeaking
    ? 'Anisha is speaking'
    : isListening
      ? 'Listening to you'
      : isThinking
        ? 'Anisha is thinking...'
        : null;

  return (
    <div className={cn(tileViewClassNames.grid)}>

      {/* Agent */}

      <div
        className={cn([
          'grid',

          !chatOpen &&
            tileViewClassNames.agentChatClosed,

          chatOpen &&
            hasSecondTile &&
            tileViewClassNames.agentChatOpenWithSecondTile,

          chatOpen &&
            !hasSecondTile &&
            tileViewClassNames.agentChatOpenWithoutSecondTile,
        ])}
      >

        {!isAvatar && (
          <motion.div
            key="agent"
            layoutId="agent"
            initial={{
              opacity: 0,
            }}
            animate={{
              opacity: 1,
            }}
            transition={{
              ...ANIMATION_TRANSITION,
              delay: animationDelay,
            }}
            className="relative aspect-square h-[90px]"
          >

            <AudioVisualizer
              key="audio-visualizer"
              initial={{
                scale: 1,
              }}
              animate={{
                scale: chatOpen ? 0.2 : 1,
              }}
              transition={{
                ...ANIMATION_TRANSITION,
                delay: animationDelay,
              }}
              audioVisualizerType={audioVisualizerType}
              audioVisualizerColor={audioVisualizerColor}
              audioVisualizerColorShift={
                audioVisualizerColorShift
              }
              audioVisualizerBarCount={
                audioVisualizerBarCount
              }
              audioVisualizerRadialBarCount={
                audioVisualizerRadialBarCount
              }
              audioVisualizerRadialRadius={
                audioVisualizerRadialRadius
              }
              audioVisualizerGridRowCount={
                audioVisualizerGridRowCount
              }
              audioVisualizerGridColumnCount={
                audioVisualizerGridColumnCount
              }
              audioVisualizerWaveLineWidth={
                audioVisualizerWaveLineWidth
              }
              isChatOpen={chatOpen}
              className={cn(
                'absolute top-1/2 left-1/2',
                '-translate-x-1/2 -translate-y-1/2',
                'bg-background rounded-[50px]',
                'border border-transparent',
                'transition-[border,drop-shadow]',
                chatOpen &&
                  'border-input shadow-2xl/10 delay-200'
              )}
              style={{
                color: audioVisualizerColor,
              }}
            />

            {/* Anisha AI Center Avatar Frame */}
            <div className="absolute top-1/2 left-1/2 z-10 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
              <div className={cn(
                "relative h-16 w-16 overflow-hidden rounded-full border-2 border-background shadow-lg transition-transform duration-300",
                chatOpen && "h-10 w-10 border-1",
                isSpeaking && "ring-4 ring-primary/40 animate-pulse",
                isListening && "ring-4 ring-emerald-500/40"
              )}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/anisha_avatar.png"
                  alt="Anisha AI"
                  className="h-full w-full object-cover"
                />
              </div>
            </div>

            {/* Speaker State Indicator (Listening to you / Anisha is speaking) */}

            <AnimatePresence mode="wait">
              {statusLabel && (
                <motion.div
                  key={statusLabel}
                  initial={{
                    opacity: 0,
                    y: 6,
                    scale: 0.94,
                  }}
                  animate={{
                    opacity: 1,
                    y: 0,
                    scale: 1,
                  }}
                  exit={{
                    opacity: 0,
                    y: -4,
                    scale: 0.94,
                  }}
                  transition={{
                    duration: 0.2,
                  }}
                  className={cn(
                    "absolute left-1/2 z-30 -translate-x-1/2 pointer-events-none transition-all duration-300",
                    chatOpen ? "top-[85px]" : "top-[160px]"
                  )}
                >

                  <div
                    className={cn(
                      'flex items-center gap-2.5',
                      'whitespace-nowrap',
                      'rounded-full border',
                      'bg-background/95',
                      'px-4 py-2',
                      'text-xs font-semibold',
                      'shadow-xl',
                      'backdrop-blur-md',

                      isSpeaking
                        ? 'border-primary/40 text-primary bg-primary/5'
                        : isListening
                          ? 'border-emerald-500/40 text-emerald-600 dark:text-emerald-400 bg-emerald-500/5'
                          : 'border-amber-500/40 text-amber-600 dark:text-amber-400 bg-amber-500/5'
                    )}
                  >

                    <motion.span
                      className={cn(
                        'size-2.5 rounded-full',

                        isSpeaking
                          ? 'bg-primary'
                          : isListening
                            ? 'bg-emerald-500'
                            : 'bg-amber-500'
                      )}
                      animate={{
                        scale: [1, 1.4, 1],
                      }}
                      transition={{
                        duration: 0.8,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }}
                    />

                    <span>{statusLabel}</span>

                    {/* Step 3: Audio Volume Waveform / Bar Visualizer */}
                    <div className="flex items-center gap-0.5 ml-1 h-3">
                      {[0.4, 0.9, 0.6, 1.0, 0.5].map((heightFactor, i) => (
                        <motion.span
                          key={i}
                          className={cn('w-0.5 h-3 rounded-full', isSpeaking ? 'bg-primary' : isListening ? 'bg-emerald-500' : 'bg-amber-500')}
                          animate={
                            isSpeaking || isListening
                              ? { height: ['20%', `${heightFactor * 100}%`, '20%'] }
                              : { height: '20%' }
                          }
                          transition={{
                            duration: 0.4 + i * 0.1,
                            repeat: Infinity,
                            repeatType: 'mirror',
                            ease: 'easeInOut',
                          }}
                        />
                      ))}
                    </div>

                  </div>

                </motion.div>
              )}
            </AnimatePresence>

          </motion.div>
        )}

        {isAvatar && (
          <motion.div
            key="avatar"
            layoutId="avatar"
            initial={{
              scale: 1,
              opacity: 1,
              maskImage:
                'radial-gradient(circle, rgba(0, 0, 0, 1) 0, rgba(0, 0, 0, 1) 20px, transparent 20px)',
              filter: 'blur(20px)',
            }}
            animate={{
              maskImage:
                'radial-gradient(circle, rgba(0, 0, 0, 1) 0, rgba(0, 0, 0, 1) 500px, transparent 500px)',
              filter: 'blur(0px)',
              borderRadius: chatOpen ? 6 : 12,
            }}
            transition={{
              ...ANIMATION_TRANSITION,
              delay: animationDelay,
              maskImage: {
                duration: 1,
              },
              filter: {
                duration: 1,
              },
            }}
            className={cn(
              'overflow-hidden',
              'bg-black',
              'drop-shadow-xl/80',
              chatOpen
                ? 'h-[90px]'
                : 'h-auto w-full'
            )}
          >

            <VideoTrack
              width={videoWidth}
              height={videoHeight}
              trackRef={agentVideoTrack}
              className={cn(
                chatOpen &&
                  'size-[90px] object-cover'
              )}
            />

          </motion.div>
        )}

      </div>

      {/* Camera / Screen Share Tile */}

      <div
        className={cn([
          'grid',

          chatOpen &&
            tileViewClassNames.secondTileChatOpen,

          !chatOpen &&
            'col-start-2 row-start-1 self-start justify-self-end p-4',
        ])}
      >

        <AnimatePresence>
          {(
            (cameraTrack && isCameraEnabled) ||
            (screenShareTrack && isScreenShareEnabled)
          ) && (
            <motion.div
              key="camera"
              layout="position"

              initial={{
                opacity: 0,
                scale: 0,
              }}
              animate={{
                opacity: 1,
                scale: 1,
              }}
              exit={{
                opacity: 0,
                scale: 0,
              }}
              transition={{
                ...ANIMATION_TRANSITION,
                delay: animationDelay,
              }}
              className="
                aspect-square
                size-[90px]
                drop-shadow-lg/20
              "
            >

              <VideoTrack
                trackRef={
                  cameraTrack ||
                  screenShareTrack
                }
                width={
                  (
                    cameraTrack ||
                    screenShareTrack
                  )?.publication.dimensions?.width ?? 0
                }
                height={
                  (
                    cameraTrack ||
                    screenShareTrack
                  )?.publication.dimensions?.height ?? 0
                }
                className="
                  bg-muted
                  aspect-square
                  size-[90px]
                  rounded-md
                  object-cover
                "
              />

            </motion.div>
          )}
        </AnimatePresence>

      </div>

    </div>
  );
}





