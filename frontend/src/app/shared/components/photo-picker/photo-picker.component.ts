import {
  Component,
  ElementRef,
  OnDestroy,
  effect,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';

@Component({
  selector: 'app-photo-picker',
  standalone: true,
  templateUrl: './photo-picker.component.html',
  styleUrl: './photo-picker.component.css',
})
export class PhotoPickerComponent implements OnDestroy {
  readonly label = input.required<string>();
  readonly photo = input<File | null>(null);
  readonly photoChange = output<File | null>();

  private cameraVideo = viewChild.required<ElementRef<HTMLVideoElement>>('cameraVideo');
  private captureCanvas = viewChild.required<ElementRef<HTMLCanvasElement>>('captureCanvas');

  preview = signal<string | null>(null);
  error = signal('');
  cameraOpen = signal(false);
  private cameraStream: MediaStream | null = null;
  private destroyed = false;

  constructor() {
    effect(() => {
      if (this.photo() === null) {
        this.clearPreview();
        this.error.set('');
      }
    });
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.fecharCamera();
    this.clearPreview();
  }

  async abrirCamera(): Promise<void> {
    this.error.set('');
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      this.error.set(
        'A câmera exige uma conexão segura (HTTPS ou localhost) e suporte do navegador.',
      );
      return;
    }

    this.fecharCamera();
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: 'user' } },
        audio: false,
      });
      if (this.destroyed) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }

      this.cameraStream = stream;
      this.cameraOpen.set(true);
      const video = this.cameraVideo().nativeElement;
      video.srcObject = stream;
      await video.play();
    } catch (error: unknown) {
      this.fecharCamera();
      this.error.set(this.mensagemErroDaCamera(error));
    }
  }

  async capturarFoto(): Promise<void> {
    const video = this.cameraVideo().nativeElement;
    const canvas = this.captureCanvas().nativeElement;
    if (!video.videoWidth || !video.videoHeight) {
      this.error.set('A câmera ainda está iniciando. Aguarde um instante e tente novamente.');
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const context = canvas.getContext('2d');
    if (!context) {
      this.error.set('Não foi possível capturar a imagem neste navegador.');
      return;
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', 0.9),
    );
    if (!blob) {
      this.error.set('Não foi possível gerar a foto capturada. Tente novamente.');
      return;
    }

    const photo = new File([blob], `foto-${Date.now()}.jpg`, {
      type: 'image/jpeg',
    });
    this.clearPreview();
    this.preview.set(URL.createObjectURL(photo));
    this.photoChange.emit(photo);
    this.error.set('');
    this.fecharCamera();
  }

  fecharCamera(): void {
    this.cameraStream?.getTracks().forEach((track) => track.stop());
    this.cameraStream = null;
    this.cameraOpen.set(false);
    this.cameraVideo().nativeElement.srcObject = null;
  }

  selecionar(event: Event): void {
    if (!(event.target instanceof HTMLInputElement)) {
      return;
    }
    const input = event.target;
    const photo = input.files?.[0] ?? null;
    input.value = '';
    if (!photo) {
      return;
    }
    if (!photo.type.startsWith('image/')) {
      this.fecharCamera();
      this.clearPreview();
      this.error.set('Selecione um arquivo de imagem válido.');
      this.photoChange.emit(null);
      return;
    }

    this.fecharCamera();
    this.clearPreview();
    this.error.set('');
    this.preview.set(URL.createObjectURL(photo));
    this.photoChange.emit(photo);
  }

  private clearPreview(): void {
    const preview = this.preview();
    if (preview) {
      URL.revokeObjectURL(preview);
      this.preview.set(null);
    }
  }

  private mensagemErroDaCamera(error: unknown): string {
    if (error instanceof DOMException) {
      if (error.name === 'NotAllowedError' || error.name === 'SecurityError') {
        return 'Acesso à câmera negado. Permita o uso da câmera nas configurações do navegador.';
      }
      if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        return 'Nenhuma câmera foi encontrada neste dispositivo.';
      }
      if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        return 'A câmera está sendo usada por outro aplicativo ou não pôde ser iniciada.';
      }
    }
    return 'Não foi possível abrir a câmera. Verifique a conexão e as permissões do navegador.';
  }
}
