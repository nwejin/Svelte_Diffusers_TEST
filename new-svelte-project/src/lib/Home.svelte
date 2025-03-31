<script lang="ts">
	import { Link } from "svelte-routing";
</script>

<div class="text-center">
	<h2 class="mb-4 text-2xl font-semibold">API 서버 선택</h2>
	<div class="flex flex-col items-center justify-center gap-4 sm:flex-row">
		<Link
			to="/diffusers"
			class="px-6 py-3 text-white bg-blue-500 rounded-lg hover:bg-blue-600"
		>
			Diffusers API
		</Link>
		<Link
			to="/compyUI"
			class="px-6 py-3 text-white bg-blue-500 rounded-lg hover:bg-blue-600"
		>
			CompyUI API
		</Link>
	</div>
</div>
