<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { toast } from 'svelte-sonner';
	
	import { models, user, chats as _chats } from '$lib/stores';
	import { getAllUserChats } from '$lib/apis/chats';
	import { getUsers } from '$lib/apis/users';
	
	const i18n = getContext('i18n');
	
	// Estrutura para armazenar os custos por modelo e por usuário
	let modelCosts = {};
	let userCosts = {};
	let totalCost = 0;
	
	// Preços por 1000 tokens para cada modelo (exemplo)
	// Estes valores devem ser ajustados de acordo com os preços reais dos modelos
	const modelPrices = {
		// OpenAI
		'gpt-4': { input: 0.03, output: 0.06 },
		'gpt-4-32k': { input: 0.06, output: 0.12 },
		'gpt-4-turbo': { input: 0.01, output: 0.03 },
		'gpt-4o': { input: 0.01, output: 0.03 },
		'gpt-3.5-turbo': { input: 0.0015, output: 0.002 },
		// Anthropic
		'claude-3-opus': { input: 0.015, output: 0.075 },
		'claude-3-sonnet': { input: 0.003, output: 0.015 },
		'claude-3-haiku': { input: 0.00025, output: 0.00125 },
		// Modelos locais (Ollama)
		'default': { input: 0, output: 0 }
	};
	
	// Função para obter o preço de um modelo
	function getModelPrice(modelId) {
		// Verificar se o modelo existe na lista de preços
		for (const key in modelPrices) {
			if (modelId && modelId.includes(key)) {
				return modelPrices[key];
			}
		}
		// Se não encontrar, retorna o preço padrão (0)
		return modelPrices['default'];
	}
	
	// Função para calcular o custo de uma mensagem
	function calculateMessageCost(message) {
		if (!message.info) return 0;
		
		const modelId = message.model;
		const modelPrice = getModelPrice(modelId);
		
		const promptTokens = message.info.prompt_tokens || 0;
		const completionTokens = message.info.completion_tokens || 0;
		
		const inputCost = (promptTokens / 1000) * modelPrice.input;
		const outputCost = (completionTokens / 1000) * modelPrice.output;
		
		return inputCost + outputCost;
	}
	
	// Função para carregar todos os chats e calcular os custos
	async function loadChatsAndCalculateCosts() {
		try {
			// Obter todos os usuários
			const usersResponse = await getUsers(localStorage.token);
			const users = usersResponse;
			
			// Obter todos os chats de todos os usuários
			const chatsResponse = await getAllUserChats(localStorage.token);
			const allChats = chatsResponse;
			
			// Inicializar estruturas de dados
			modelCosts = {};
			userCosts = {};
			totalCost = 0;
			
			// Inicializar custo para cada usuário
			for (const user of users) {
				const userId = user.id;
				const userName = user.name;
				
				userCosts[userId] = {
					username: userName,
					totalCost: 0,
					models: {}
				};
			}
			
			// Processar todos os chats
			for (const chat of allChats) {
				const userId = chat.user_id;
				const userName = users.find(u => u.id === userId)?.name || 'Usuário Desconhecido';
				
				// Verificar se o usuário existe na estrutura de custos
				if (!userCosts[userId]) {
					userCosts[userId] = {
						username: userName,
						totalCost: 0,
						models: {}
					};
				}
				
				// Processar as mensagens do chat
				if (chat.chat && chat.chat.history && chat.chat.history.messages) {
					const messages = Object.values(chat.chat.history.messages);
					
					for (const message of messages) {
						if (message.role === 'assistant') {
							const modelId = message.model || 'desconhecido';
							const cost = calculateMessageCost(message);
							
							// Atualizar custo total
							totalCost += cost;
							
							// Atualizar custo por modelo
							if (!modelCosts[modelId]) {
								modelCosts[modelId] = {
									totalCost: 0,
									users: {}
								};
							}
							modelCosts[modelId].totalCost += cost;
							
							// Atualizar custo do modelo para o usuário
							if (!modelCosts[modelId].users[userId]) {
								modelCosts[modelId].users[userId] = {
									username: userName,
									cost: 0
								};
							}
							modelCosts[modelId].users[userId].cost += cost;
							
							// Atualizar custo do usuário
							userCosts[userId].totalCost += cost;
							
							// Atualizar custo do modelo para o usuário
							if (!userCosts[userId].models[modelId]) {
								userCosts[userId].models[modelId] = 0;
							}
							userCosts[userId].models[modelId] += cost;
						}
					}
				}
			}
		} catch (error) {
			console.error('Erro ao carregar chats:', error);
			toast.error($i18n.t('Erro ao carregar dados de custo'));
		}
	}
	
	// Formatar valor monetário
	function formatCurrency(value) {
		return new Intl.NumberFormat('pt-PT', {
			style: 'currency',
			currency: 'EUR'
		}).format(value);
	}
	
	onMount(async () => {
		await loadChatsAndCalculateCosts();
	});
</script>

<div class="flex flex-col w-full">
	<div class="flex justify-between items-center mb-4">
		<h1 class="text-2xl font-bold">{$i18n.t('Custos de Modelos')}</h1>
		<button 
			class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
			on:click={loadChatsAndCalculateCosts}
		>
			{$i18n.t('Atualizar')}
		</button>
	</div>
	
	<div class="bg-white dark:bg-gray-800 rounded-lg p-4 mb-6 shadow">
		<h2 class="text-xl font-semibold mb-2">{$i18n.t('Custo Total')}</h2>
		<p class="text-3xl font-bold text-blue-600 dark:text-blue-400">{formatCurrency(totalCost)}</p>
	</div>
	
	<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
		<!-- Custos por Modelo -->
		<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
			<h2 class="text-xl font-semibold mb-4">{$i18n.t('Custos por Modelo')}</h2>
			
			{#if Object.keys(modelCosts).length === 0}
				<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Nenhum dado disponível')}</p>
			{:else}
				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr class="border-b dark:border-gray-700">
								<th class="text-left py-2">{$i18n.t('Modelo')}</th>
								<th class="text-right py-2">{$i18n.t('Custo')}</th>
							</tr>
						</thead>
						<tbody>
							{#each Object.entries(modelCosts).sort((a, b) => b[1].totalCost - a[1].totalCost) as [modelId, data]}
								<tr class="border-b dark:border-gray-700">
									<td class="py-2">{modelId}</td>
									<td class="text-right py-2">{formatCurrency(data.totalCost)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
		
		<!-- Custos por Usuário -->
		<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
			<h2 class="text-xl font-semibold mb-4">{$i18n.t('Custos por Usuário')}</h2>
			
			{#if Object.keys(userCosts).length === 0}
				<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Nenhum dado disponível')}</p>
			{:else}
				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr class="border-b dark:border-gray-700">
								<th class="text-left py-2">{$i18n.t('Usuário')}</th>
								<th class="text-right py-2">{$i18n.t('Custo')}</th>
							</tr>
						</thead>
						<tbody>
							{#each Object.entries(userCosts).sort((a, b) => b[1].totalCost - a[1].totalCost) as [userId, data]}
								<tr class="border-b dark:border-gray-700">
									<td class="py-2">{data.username}</td>
									<td class="text-right py-2">{formatCurrency(data.totalCost)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	</div>
	
	<!-- Detalhes por Modelo -->
	<div class="mt-6">
		<h2 class="text-xl font-semibold mb-4">{$i18n.t('Detalhes por Modelo')}</h2>
		
		{#if Object.keys(modelCosts).length === 0}
			<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Nenhum dado disponível')}</p>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each Object.entries(modelCosts).sort((a, b) => b[1].totalCost - a[1].totalCost) as [modelId, data]}
					<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
						<h3 class="font-semibold text-lg mb-2">{modelId}</h3>
						<p class="text-blue-600 dark:text-blue-400 font-bold mb-3">{formatCurrency(data.totalCost)}</p>
						
						<h4 class="font-medium mb-2">{$i18n.t('Usuários')}</h4>
						<div class="overflow-y-auto max-h-40">
							<table class="w-full">
								<thead>
									<tr class="border-b dark:border-gray-700">
										<th class="text-left py-1 text-sm">{$i18n.t('Usuário')}</th>
										<th class="text-right py-1 text-sm">{$i18n.t('Custo')}</th>
									</tr>
								</thead>
								<tbody>
									{#each Object.entries(data.users).sort((a, b) => b[1].cost - a[1].cost) as [userId, userData]}
										<tr class="border-b dark:border-gray-700">
											<td class="py-1 text-sm">{userData.username}</td>
											<td class="text-right py-1 text-sm">{formatCurrency(userData.cost)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
	
	<!-- Detalhes por Usuário -->
	<div class="mt-6 mb-8">
		<h2 class="text-xl font-semibold mb-4">{$i18n.t('Detalhes por Usuário')}</h2>
		
		{#if Object.keys(userCosts).length === 0}
			<p class="text-gray-500 dark:text-gray-400">{$i18n.t('Nenhum dado disponível')}</p>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each Object.entries(userCosts).sort((a, b) => b[1].totalCost - a[1].totalCost) as [userId, data]}
					<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
						<h3 class="font-semibold text-lg mb-2">{data.username}</h3>
						<p class="text-blue-600 dark:text-blue-400 font-bold mb-3">{formatCurrency(data.totalCost)}</p>
						
						<h4 class="font-medium mb-2">{$i18n.t('Modelos')}</h4>
						<div class="overflow-y-auto max-h-40">
							<table class="w-full">
								<thead>
									<tr class="border-b dark:border-gray-700">
										<th class="text-left py-1 text-sm">{$i18n.t('Modelo')}</th>
										<th class="text-right py-1 text-sm">{$i18n.t('Custo')}</th>
									</tr>
								</thead>
								<tbody>
									{#each Object.entries(data.models).sort((a, b) => b[1] - a[1]) as [modelId, cost]}
										<tr class="border-b dark:border-gray-700">
											<td class="py-1 text-sm">{modelId}</td>
											<td class="text-right py-1 text-sm">{formatCurrency(cost)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div> 