<script lang="ts">
	import { onMount } from "svelte";
	import {
		UserRound,
		ArrowRight,
		ArrowLeft,
		Check,
		Wifi,
		WifiOff,
	} from "lucide-svelte";
	import { promptConfig } from "../config";

	const { promptOptions, defaultSelections } = promptConfig;

	interface PromptCache {
		lastPromptId?: string;
	}

	const promptCache: PromptCache = {};

	// 프롬프트 옵션값 관련
	// 선택 옵션 (값은 영어로 저장)
	let selectedGender = defaultSelections.selectedGender;
	let selectedAge = defaultSelections.selectedAge;
	let selectedTheme = defaultSelections.selectedTheme;
	let selectedClass = defaultSelections.selectedClass;

	// 외형
	let selectedBodyType = defaultSelections.selectedBodyType;
	let selectedClothing = defaultSelections.selectedClothing;
	let selectedHairColor = defaultSelections.selectedHairColor;
	let selectedHairLength = defaultSelections.selectedHairLength;
	let selectedHairCurl = defaultSelections.selectedHairCurl;
	let selectedEyeColor = defaultSelections.selectedEyeColor;
	let selectedEyeSize = defaultSelections.selectedEyeSize;

	// 배경
	let selectedFamily = defaultSelections.selectedFamily;
	let selectedFamilyHistory = defaultSelections.selectedFamilyHistory;
	let selectedRegion = defaultSelections.selectedRegion;
	let selectedPersonality = defaultSelections.selectedPersonality;

	// 생성 관련
	let isLoading = false;
	let generatedImage: string | null = null;
	let errorMessage: string | null = null;
	let currentStep = 0;
	let seedValue: number | null = null;
	let progressPercent = 0; // 진행률 표시용

	const steps = [
		{ name: "기본 정보" },
		{ name: "외형" },
		{ name: "배경" },
		{ name: "확인" },
	];

	interface Option {
		value: string;
		label: string;
	}

	const getOptionLabel = (optionArray: Option[], value: string): string => {
		const option = optionArray.find((opt) => opt.value === value);
		return option ? option.label : String(value);
	};

	const nextStep = () => {
		if (currentStep < steps.length - 1) {
			currentStep++;
		}
	};

	const prevStep = () => {
		if (currentStep > 0) {
			currentStep--;
		}
	};

	// ComfyUI 웹소켓
	let websocket: WebSocket | null = null;
	let isConnected = false;
	let connectionStatus = "연결 시도 중..."; // 연결 상태 메시지

	const connectWebSocket = () => {
		if (isConnected && websocket) return;

		try {
			connectionStatus = "연결 시도 중...";
			websocket = new WebSocket("ws://localhost:8188/ws");

			websocket.onopen = () => {
				console.log("웹소켓 연결 성공");
				isConnected = true;
				connectionStatus = "연결";
			};

			websocket.onclose = () => {
				console.log("웹소켓 연결 종료");
				isConnected = false;
				connectionStatus = "연결 끊김";
				websocket = null;

				// 5초 후 재연결 시도
				setTimeout(connectWebSocket, 5000);
			};

			websocket.onerror = (error) => {
				console.error("웹소켓 오류:", error);
				isConnected = false;
				connectionStatus = "연결 오류";
				websocket = null;
			};

			websocket.onmessage = (event) => {
				try {
					const message = JSON.parse(event.data);
					console.log("웹소켓 메시지:", message);

					handleWebSocketMessage(message);
				} catch (error) {
					console.error("웹소켓 메시지 처리 오류:", error);
				}
			};
		} catch (error) {
			console.error("웹소켓 연결 시도 오류:", error);
			connectionStatus = "연결 실패";
			setTimeout(connectWebSocket, 5000);
		}
	};

	const handleWebSocketMessage = (message: any) => {
		console.log("웹소켓 메시지:", message);

		// 실행 완료 메시지인 경우
		if (message.type === "execution_complete") {
			const promptId = message.data.prompt_id;
			console.log(`워크플로우 실행 완료 (ID: ${promptId})`);

			// 히스토리 데이터가 업데이트될 시간을 주기 위해 약간 지연 후 폴링 시작
		}

		// 실행 중인 메시지인 경우 (현재 진행 중인 노드 표시 용도)
		if (message.type === "executing") {
			const { node } = message.data;
			console.log(`노드 실행 중: ${node}`);
		}

		// 큐 상태 메시지인 경우
		if (message.type === "status") {
			console.log("큐 상태:", message.data);
		}
	};

	// 이미지 생성 완료 후 히스토리 데이터 폴링 함수
	async function pollHistoryData(promptId: string, maxAttempts = 10) {
		let attempts = 0;

		const checkHistory = async () => {
			try {
				console.log(`히스토리 데이터 확인 시도 ${attempts + 1}/${maxAttempts}`);

				const historyResponse = await fetch(
					`http://localhost:8188/history/${promptId}`,
					{ cache: "no-store" },
				);

				if (!historyResponse.ok) {
					throw new Error("히스토리 정보를 가져오는데 실패했습니다.");
				}

				const historyData = await historyResponse.json();
				console.log("히스토리 데이터:", historyData);

				// 히스토리 데이터가 비어있지 않고 outputs 속성이 있는지 확인
				if (
					historyData &&
					Object.keys(historyData).length > 0 &&
					historyData[promptId] &&
					historyData[promptId].outputs
				) {
					// 이미지 정보 처리
					for (const nodeId in historyData[promptId].outputs) {
						const nodeOutput = historyData[promptId].outputs[nodeId];
						if (
							nodeOutput &&
							nodeOutput.images &&
							nodeOutput.images.length > 0
						) {
							const image = nodeOutput.images[0];
							const imageName = image.filename;
							const imageUrl = `http://localhost:8188/view?filename=${encodeURIComponent(imageName)}`;

							console.log("이미지 URL 생성됨:", imageUrl);
							generatedImage = imageUrl;

							// 시드 값 찾기
							try {
								if (
									historyData[promptId].prompt &&
									historyData[promptId].prompt[2] &&
									historyData[promptId].prompt[2]["3"]
								) {
									seedValue = historyData[promptId].prompt[2]["3"].inputs.seed;
									console.log("시드 값:", seedValue);
								}
							} catch (error) {
								console.error("시드 값 찾기 오류:", error);
							}

							// 로딩 상태 종료
							isLoading = false;
							progressPercent = 0;
							return true;
						}
					}
				}

				// 아직 데이터가 없거나 이미지를 찾지 못한 경우
				attempts++;
			} catch (error) {
				console.error("히스토리 데이터 폴링 오류:", error);
				attempts++;
				if (attempts < maxAttempts && isLoading) {
					// 오류 발생 시 1.5초 후 다시 시도
					setTimeout(checkHistory, 1500);
				} else {
					errorMessage =
						error instanceof Error
							? error.message
							: "알 수 없는 오류가 발생했습니다.";
					isLoading = false;
				}
			}
		};

		// 첫 번째 시도 시작
		checkHistory();
	}

	// 생성된 이미지 정보 가져오기 (이전 메서드, 이제 pollHistoryData로 대체됨)
	async function fetchGeneratedImage(promptId: string) {
		try {
			const historyResponse = await fetch(
				`http://localhost:8188/history/${promptId}`,
				{ cache: "no-store" },
			);

			if (!historyResponse.ok) {
				throw new Error("히스토리 정보를 가져오는데 실패했습니다.");
			}

			const historyData = await historyResponse.json();
			console.log("히스토리 데이터:", historyData);

			// 출력에서 이미지 찾기
			if (historyData.outputs) {
				for (const nodeId in historyData.outputs) {
					const nodeOutput = historyData.outputs[nodeId];
					if (nodeOutput && nodeOutput.images && nodeOutput.images.length > 0) {
						const image = nodeOutput.images[0];
						const imageName = image.filename;
						const imageUrl = `http://localhost:8188/view?filename=${encodeURIComponent(imageName)}`;

						console.log("이미지 생성 완료:", imageUrl);
						generatedImage = imageUrl;

						// 시드 값 찾기
						try {
							if (
								historyData.prompt &&
								historyData.prompt[2] &&
								historyData.prompt[2]["3"]
							) {
								seedValue = historyData.prompt[2]["3"].inputs.seed;
								console.log("시드 값:", seedValue);
							}
						} catch (error) {
							console.error("시드 값 찾기 오류:", error);
						}

						// 로딩 상태 종료
						isLoading = false;
						progressPercent = 0;
						return true;
					}
				}
			}

			// 이미지를 찾지 못한 경우
			console.warn("이미지를 찾지 못했습니다:", historyData);
			return false;
		} catch (error) {
			console.error("이미지 정보 가져오기 오류:", error);
			errorMessage =
				error instanceof Error
					? error.message
					: "이미지 정보를 가져오는데 실패했습니다.";
			isLoading = false;
			return false;
		}
	}

	// 프롬프트 생성
	const generatePrompt = (): string => {
		return `(masterpiece, best quality, high detail, anime, grey background, from head to toe), 
		a ${selectedAge} ${selectedBodyType} ${selectedGender} character in ${selectedTheme} setting, 
		wearing a ${selectedClothing}, with ${selectedHairColor} ${selectedHairLength} hair (${selectedHairCurl}), 
		${selectedEyeColor} eyes, ${selectedEyeSize} eyes, detailed facial features, ultra HD`;
	};

	async function generateImage() {
		isLoading = true;
		generatedImage = null;
		errorMessage = null;
		progressPercent = 0;

		try {
			const positivePrompt = generatePrompt();
			const negativePrompt =
				"((bad hands:1)), ((extra fingers:1)), ((deformed hands:1)), ((unhealthy hands:1)), ((excess limbs:1.1)),((lowres)),((worst quality)), ((bad quality)), ((low quality)), naked, nsfw";

			const workflow = {
				"3": {
					inputs: {
						seed: Math.floor(Math.random() * 1000000000000000),
						steps: 20,
						cfg: 8,
						sampler_name: "euler",
						scheduler: "normal",
						denoise: 1,
						model: ["4", 0],
						positive: ["6", 0],
						negative: ["7", 0],
						latent_image: ["5", 0],
					},
					class_type: "KSampler",
					_meta: {
						title: "KSampler",
					},
				},
				"4": {
					inputs: {
						ckpt_name: "v1-5-pruned-emaonly.safetensors",
					},
					class_type: "CheckpointLoaderSimple",
					_meta: {
						title: "Load Checkpoint",
					},
				},
				"5": {
					inputs: {
						width: 512,
						height: 768,
						batch_size: 1,
					},
					class_type: "EmptyLatentImage",
					_meta: {
						title: "Empty Latent Image",
					},
				},
				"6": {
					inputs: {
						text: positivePrompt,
						clip: ["4", 1],
					},
					class_type: "CLIPTextEncode",
					_meta: {
						title: "CLIP Text Encode (Prompt)",
					},
				},
				"7": {
					inputs: {
						text: negativePrompt,
						clip: ["4", 1],
					},
					class_type: "CLIPTextEncode",
					_meta: {
						title: "CLIP Text Encode (Negative Prompt)",
					},
				},
				"8": {
					inputs: {
						samples: ["3", 0],
						vae: ["4", 2],
					},
					class_type: "VAEDecode",
					_meta: {
						title: "VAE Decode",
					},
				},
				"9": {
					inputs: {
						filename_prefix: "ComfyUI",
						images: ["8", 0],
					},
					class_type: "SaveImage",
					_meta: {
						title: "Save Image",
					},
				},
			};

			const promptData = {
				prompt: workflow,
				client_id: `svelte_${Date.now()}`,
			};

			console.log("이미지 생성 프롬프트 전송:", promptData);

			// ComfyUI API 직접 호출 대신 FastAPI 서버 호출
			const response = await fetch("http://localhost:8000/api/generate-image", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(promptData),
			});

			if (!response.ok) {
				throw new Error(
					`API 요청 실패: ${response.status} ${response.statusText}`,
				);
			}

			const data = await response.json();
			console.log("API 응답:", data);

			const promptId = data.prompt_id;
			console.log("프롬프트ID:", promptId);

			// 전역 변수에 promptId 저장
			promptCache.lastPromptId = promptId;

			// 주기적으로 히스토리 확인
			const checkInterval = setInterval(async () => {
				if (!isLoading) {
					clearInterval(checkInterval);
					return;
				}

				try {
					// FastAPI 서버에서 히스토리 가져오기
					const historyResponse = await fetch(
						`http://localhost:8000/api/history/${promptId}`,
						{ cache: "no-store" },
					);

					if (!historyResponse.ok) {
						throw new Error("히스토리 정보를 가져오는데 실패했습니다.");
					}

					const historyData = await historyResponse.json();

					// 이미지 정보 찾기
					if (
						historyData &&
						historyData[promptId] &&
						historyData[promptId].outputs
					) {
						for (const nodeId in historyData[promptId].outputs) {
							const nodeOutput = historyData[promptId].outputs[nodeId];
							if (
								nodeOutput &&
								nodeOutput.images &&
								nodeOutput.images.length > 0
							) {
								const image = nodeOutput.images[0];
								const imageName = image.filename;

								// FastAPI 이미지 URL로 변경
								const imageUrl = `http://localhost:8000/api/image?filename=${encodeURIComponent(imageName)}`;

								console.log("이미지 생성 완료:", imageUrl);
								generatedImage = imageUrl;

								// 시드 값 찾기
								try {
									if (
										historyData[promptId].prompt &&
										historyData[promptId].prompt["3"]
									) {
										seedValue = historyData[promptId].prompt["3"].inputs.seed;
										console.log("시드 값:", seedValue);
									}
								} catch (error) {
									console.error("시드 값 찾기 오류:", error);
								}

								// 로딩 상태 종료
								isLoading = false;
								progressPercent = 0;
								clearInterval(checkInterval);
								return;
							}
						}
					}

					// 이미지를 아직 찾지 못함, 계속 확인
					console.log("이미지 생성 중...");
				} catch (error) {
					console.error("히스토리 확인 오류:", error);
					isLoading = false;
					clearInterval(checkInterval);
				}
			}, 1000); // 1초마다 확인
		} catch (error) {
			console.error("이미지 생성 중 오류:", error);
			errorMessage =
				error instanceof Error
					? error.message
					: "알 수 없는 오류가 발생했습니다.";
			isLoading = false;
		}
	}
</script>

<h2 class="mb-4 text-3xl font-semibold text-gray-600">
	CompyUI 예시코드를 활용한 이미지 생성
</h2>
<div class="grid w-full grid-cols-2 gap-8 p-4">
	<!-- 왼쪽 컬럼: 단계별 입력 폼 -->
	<div class="p-6 bg-white shadow-lg rounded-xl">
		<!-- <div class="flex items-center justify-end mb-2">
			<div
				class="flex items-center gap-2 px-3 py-1 text-sm rounded-full {isConnected
					? 'bg-green-100 text-green-700'
					: 'bg-red-100 text-red-700'}"
			>
				{#if isConnected}
					<Wifi size={16} />
				{:else}
					<WifiOff size={16} />
				{/if}
				<span>{connectionStatus}</span>
				{#if !isConnected}
					<button
						on:click={reconnectServer}
						class="px-2 py-0.5 ml-2 text-xs text-white bg-blue-500 rounded hover:bg-blue-600"
					>
						연결
					</button>
				{/if}
			</div>
		</div> -->
		<!-- 스텝 인디케이터 -->
		<div class="mb-6">
			<div class="flex justify-between mb-4">
				{#each steps as step, index}
					<div
						class="flex flex-col items-center"
						class:text-blue-600={currentStep >= index}
						class:text-gray-400={currentStep < index}
					>
						<button
							class="flex items-center justify-center w-10 h-10 mb-2 border-2 rounded-full"
							class:border-blue-600={currentStep >= index}
							class:bg-blue-600={currentStep > index}
							class:border-gray-300={currentStep < index}
							on:click={() => {
								currentStep = index;
							}}
						>
							{#if currentStep > index}
								<Check class="text-white" size={18} />
							{:else}
								<span>{index + 1}</span>
							{/if}
						</button>
						<span class="text-sm">{step.name}</span>
					</div>

					{#if index < steps.length - 1}
						<div class="flex-grow pt-5">
							<div class="h-0.5 bg-gray-300"></div>
						</div>
					{/if}
				{/each}
			</div>
		</div>

		<!-- 단계별 폼 내용 -->
		<div class="min-h-[400px]">
			{#if currentStep === 0}
				<!-- 성별 선택 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">성별</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.genderOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedGender ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedGender = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 나이 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">나이</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.ageOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedAge ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedAge = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 테마 및 세계관 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">
						테마 및 세계관
					</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.themeOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedTheme ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedTheme = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 직업 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">직업</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.classOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedClass ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedClass = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>
				<!-- 랜덤 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">
						사용자 지정 프롬프트
					</h3>
					<div class="flex flex-wrap gap-2">
						<textarea
							name="randomPrompt"
							id="randomPrompt"
							class="w-full px-4 py-2 text-sm text-gray-700 transition-colors duration-200 bg-white border border-gray-300 rounded-lg resize-none hover:bg-gray-100"
						></textarea>
						<!-- {#each promptOptions.classOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedClass ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedClass = option.value)}
							>
								{option.label}
							</button>
						{/each} -->
					</div>
				</div>
			{:else if currentStep === 1}
				<!-- 체형 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">체형</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.bodyTypeOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedBodyType ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedBodyType = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 의상 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">의상</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.clothingOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedClothing ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedClothing = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">머리색</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.hairColorOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedHairColor ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedHairColor = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<div class="flex justify-between">
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">머리길이</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.hairLengthOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedHairLength ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedHairLength = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">머릿결</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.hairCurlOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedHairCurl ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedHairCurl = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
				</div>

				<div class="flex justify-between">
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">눈동자 색</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.eyeColorOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedEyeColor ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedEyeColor = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">눈 크기</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.eyeSizeOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedEyeSize ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedEyeSize = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
				</div>
			{:else if currentStep === 2}
				<!-- 가족 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">가족</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.familyOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedFamily ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedFamily = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 가문의 역사 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">가문의 역사</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.familyHistoryOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedFamilyHistory ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedFamilyHistory = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 출신 지역 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">출신 지역</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.regionOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedRegion ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedRegion = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 성격 유형 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">성격 유형</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.personalityOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedPersonality ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedPersonality = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>
			{:else if currentStep === 3}
				<div class="p-4 space-y-4 rounded-lg bg-gray-50">
					<!-- 모든 선택 항목 요약 표시 -->
					<div class="grid grid-cols-2 gap-4">
						<div class="flex flex-col">
							<span class="text-sm text-gray-500">성별</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.genderOptions,
									selectedGender,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">나이</span>
							<span class="font-medium"
								>{getOptionLabel(promptOptions.ageOptions, selectedAge)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">테마 및 세계관</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.themeOptions,
									selectedTheme,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">직업</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.classOptions,
									selectedClass,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">체형</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.bodyTypeOptions,
									selectedBodyType,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">의상</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.clothingOptions,
									selectedClothing,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">머리색</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.hairColorOptions,
									selectedHairColor,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">머리길이</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.hairLengthOptions,
									selectedHairLength,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">머릿결</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.hairCurlOptions,
									selectedHairCurl,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">눈동자색</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.eyeColorOptions,
									selectedEyeColor,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">눈크기</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.eyeSizeOptions,
									selectedEyeSize,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">가족</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.familyOptions,
									selectedFamily,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">가문의 역사</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.familyHistoryOptions,
									selectedFamilyHistory,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">출신 지역</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.regionOptions,
									selectedRegion,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">성격 유형</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.personalityOptions,
									selectedPersonality,
								)}</span
							>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- 단계 버튼 -->
		<div class="flex justify-between pt-6 mt-6 border-t border-gray-200">
			<button
				on:click={prevStep}
				class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-opacity-50 {currentStep ===
				0
					? 'opacity-0'
					: 'opacity-100'}"
				disabled={currentStep === 0}
			>
				<ArrowLeft size={16} class="mr-1" />
				이전
			</button>

			{#if currentStep === steps.length - 1}
				<button
					on:click={generateImage}
					disabled={isLoading}
					class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{isLoading ? "캐릭터 생성 중..." : "캐릭터 생성하기"}
				</button>
			{:else}
				<button
					on:click={nextStep}
					class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
				>
					다음
					<ArrowRight size={16} class="ml-1" />
				</button>
			{/if}
		</div>
	</div>

	<div class="flex flex-col w-full gap-6">
		<div class="w-full p-4 text-center bg-white shadow-lg rounded-xl">
			<!-- <h2 class="mb-2 text-xl font-bold text-gray-800">캐릭터 결과</h2> -->

			<div class="flex flex-col items-center justify-center w-full h-full">
				{#if isLoading}
					<div class="text-center">
						<p class="mb-3 text-gray-700">캐릭터를 생성하는 중입니다...</p>

						<!-- 진행률 표시 -->
						{#if progressPercent > 0}
							<div class="w-full max-w-md mx-auto mb-4">
								<div
									class="relative h-4 overflow-hidden bg-gray-200 rounded-full"
								>
									<div
										class="absolute top-0 left-0 h-full bg-blue-600 rounded-full"
										style="width: {progressPercent}%"
									></div>
								</div>
								<p class="mt-1 text-sm text-gray-600">
									{progressPercent}% 완료
								</p>
							</div>
						{:else}
							<div
								class="inline-block w-12 h-12 mt-2 border-4 border-blue-200 rounded-full border-l-blue-600 animate-spin"
							></div>
						{/if}
					</div>
				{:else if !generatedImage && !errorMessage}
					<div
						class="flex items-center justify-center w-full max-w-md bg-gray-100 rounded-lg aspect-square"
					>
						<div class="flex flex-col items-center text-gray-400">
							<UserRound size={100} />
						</div>
					</div>
				{:else if errorMessage}
					<div class="w-full p-4 text-red-700 rounded-lg bg-red-50">
						<p>오류 발생: {errorMessage}</p>
						<!-- {#if !isConnected}
							<button
								on:click={reconnectServer}
								class="px-4 py-2 mt-3 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
							>
								서버 연결 시도
							</button>
						{/if} -->
					</div>
				{:else if generatedImage}
					<div class="text-center">
						<img
							src="http://localhost:8188/view?filename=ComfyUI_00016_.png"
							alt="생성된 캐릭터"
							class="object-contain rounded-lg shadow-lg max-w-full max-h-[500px]"
						/>
						{#if seedValue}
							<p class="mt-2 text-gray-700">시드: {seedValue}</p>
						{/if}
						<div class="mt-4">
							<a
								href={generatedImage}
								download="generated-character.png"
								class="inline-flex items-center px-6 py-3 font-medium text-white transition duration-200 bg-green-600 rounded-lg hover:bg-green-700"
							>
								저장하기
							</a>
							<button
								on:click={generateImage}
								disabled={isLoading || !isConnected}
								class="inline-flex items-center px-6 py-3 ml-2 font-medium text-white transition duration-200 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								다시 생성
							</button>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
