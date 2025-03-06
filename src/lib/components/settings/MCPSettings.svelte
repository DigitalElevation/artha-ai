<script lang="ts">
	import { onMount } from 'svelte';
	import { t } from 'svelte-i18n';
	import { toast } from 'svelte-sonner';
	import { getMCPConfig, updateMCPConfig, verifyMCPConnection } from '$lib/apis/mcp';
	import { userStore } from '$lib/stores';
	import { Button, Input, Toggle } from '$lib/components/common';
	import { Trash, Plus, Check, X } from 'lucide-svelte';

	let loading = true;
	let saving = false;
	let verifying = false;
	let verifyingIndex = -1;

	let config = {
		ENABLE_MCP_API: false,
		MCP_BASE_URLS: [],
		MCP_API_CONFIGS: {}
	};

	let newUrl = '';
	let newApiKey = '';

	onMount(async () => {
		try {
			const res = await getMCPConfig($userStore?.token);
			config = res;
		} catch (error) {
			console.error(error);
			toast.error($t('Failed to load MCP configuration'));
		} finally {
			loading = false;
		}
	});

	const handleSave = async () => {
		saving = true;
		try {
			await updateMCPConfig($userStore?.token, config);
			toast.success($t('MCP configuration saved successfully'));
		} catch (error) {
			console.error(error);
			toast.error($t('Failed to save MCP configuration'));
		} finally {
			saving = false;
		}
	};

	const handleAddUrl = () => {
		if (!newUrl) return;

		// Adiciona a nova URL
		config.MCP_BASE_URLS = [...config.MCP_BASE_URLS, newUrl];

		// Adiciona a configuração da API para a nova URL
		const newIndex = config.MCP_BASE_URLS.length - 1;
		config.MCP_API_CONFIGS = {
			...config.MCP_API_CONFIGS,
			[newIndex]: {
				api_key: newApiKey
			}
		};

		// Limpa os campos
		newUrl = '';
		newApiKey = '';
	};

	const handleRemoveUrl = (index: number) => {
		// Remove a URL
		config.MCP_BASE_URLS = config.MCP_BASE_URLS.filter((_, i) => i !== index);

		// Reorganiza as configurações da API
		const newConfigs = {};
		Object.keys(config.MCP_API_CONFIGS).forEach((key) => {
			const keyIndex = parseInt(key);
			if (keyIndex < index) {
				newConfigs[keyIndex] = config.MCP_API_CONFIGS[keyIndex];
			} else if (keyIndex > index) {
				newConfigs[keyIndex - 1] = config.MCP_API_CONFIGS[keyIndex];
			}
		});
		config.MCP_API_CONFIGS = newConfigs;
	};

	const handleVerifyConnection = async (index: number) => {
		verifying = true;
		verifyingIndex = index;
		try {
			const url = config.MCP_BASE_URLS[index];
			const apiKey = config.MCP_API_CONFIGS[index]?.api_key || '';
			await verifyMCPConnection($userStore?.token, url, apiKey);
			toast.success($t('MCP connection verified successfully'));
		} catch (error) {
			console.error(error);
			toast.error($t('Failed to verify MCP connection'));
		} finally {
			verifying = false;
			verifyingIndex = -1;
		}
	};

	const handleUpdateApiKey = (index: number, value: string) => {
		config.MCP_API_CONFIGS = {
			...config.MCP_API_CONFIGS,
			[index]: {
				...config.MCP_API_CONFIGS[index],
				api_key: value
			}
		};
	};
</script>

<div class="flex flex-col space-y-4 p-4">
	<div class="flex flex-col space-y-2">
		<h2 class="text-xl font-bold">{$t('MCP Configuration')}</h2>
		<p class="text-sm text-gray-500 dark:text-gray-400">
			{$t('Configure MCP (Model Control Protocol) servers to use with Open WebUI')}
		</p>
	</div>

	{#if loading}
		<div class="flex justify-center items-center h-32">
			<div class="loader" />
		</div>
	{:else}
		<div class="flex flex-col space-y-4">
			<div class="flex items-center space-x-2">
				<Toggle
					id="enable-mcp"
					bind:checked={config.ENABLE_MCP_API}
					label={$t('Enable MCP API')}
				/>
			</div>

			{#if config.ENABLE_MCP_API}
				<div class="flex flex-col space-y-4">
					<div class="flex flex-col space-y-2">
						<h3 class="text-lg font-semibold">{$t('MCP Servers')}</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							{$t('Add MCP servers to connect to')}
						</p>
					</div>

					<div class="flex flex-col space-y-4">
						{#each config.MCP_BASE_URLS as url, index}
							<div class="flex flex-col space-y-2 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
								<div class="flex items-center justify-between">
									<h4 class="font-medium">{$t('Server')} {index + 1}</h4>
									<button
										class="text-red-500 hover:text-red-600"
										on:click={() => handleRemoveUrl(index)}
										disabled={saving}
									>
										<Trash size={16} />
									</button>
								</div>

								<div class="flex flex-col space-y-2">
									<Input
										id={`url-${index}`}
										label={$t('URL')}
										placeholder="https://api.example.com"
										bind:value={config.MCP_BASE_URLS[index]}
										disabled={saving}
									/>

									<Input
										id={`api-key-${index}`}
										label={$t('API Key (Optional)')}
										placeholder={$t('Enter API key')}
										type="password"
										value={config.MCP_API_CONFIGS[index]?.api_key || ''}
										on:input={(e) => handleUpdateApiKey(index, e.target.value)}
										disabled={saving}
									/>

									<div class="flex justify-end">
										<Button
											variant="outline"
											size="sm"
											on:click={() => handleVerifyConnection(index)}
											disabled={verifying || saving}
										>
											{#if verifying && verifyingIndex === index}
												<div class="loader-sm mr-2" />
											{/if}
											{$t('Verify Connection')}
										</Button>
									</div>
								</div>
							</div>
						{/each}

						<div class="flex flex-col space-y-2 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
							<h4 class="font-medium">{$t('Add New Server')}</h4>

							<div class="flex flex-col space-y-2">
								<Input
									id="new-url"
									label={$t('URL')}
									placeholder="https://api.example.com"
									bind:value={newUrl}
									disabled={saving}
								/>

								<Input
									id="new-api-key"
									label={$t('API Key (Optional)')}
									placeholder={$t('Enter API key')}
									type="password"
									bind:value={newApiKey}
									disabled={saving}
								/>

								<div class="flex justify-end">
									<Button
										variant="outline"
										size="sm"
										on:click={handleAddUrl}
										disabled={!newUrl || saving}
									>
										<Plus size={16} class="mr-2" />
										{$t('Add Server')}
									</Button>
								</div>
							</div>
						</div>
					</div>
				</div>
			{/if}

			<div class="flex justify-end space-x-2">
				<Button variant="primary" on:click={handleSave} disabled={saving}>
					{#if saving}
						<div class="loader-sm mr-2" />
					{/if}
					{$t('Save Configuration')}
				</Button>
			</div>
		</div>
	{/if}
</div>

<style>
	.loader {
		border: 4px solid rgba(0, 0, 0, 0.1);
		border-left-color: #3498db;
		border-radius: 50%;
		width: 30px;
		height: 30px;
		animation: spin 1s linear infinite;
	}

	.loader-sm {
		border: 2px solid rgba(0, 0, 0, 0.1);
		border-left-color: #3498db;
		border-radius: 50%;
		width: 16px;
		height: 16px;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		0% {
			transform: rotate(0deg);
		}
		100% {
			transform: rotate(360deg);
		}
	}

	:global(.dark) .loader,
	:global(.dark) .loader-sm {
		border-color: rgba(255, 255, 255, 0.1);
		border-left-color: #3498db;
	}
</style> 